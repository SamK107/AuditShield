# store/services/cinetpay.py
import json
import logging
import os
from decimal import Decimal, InvalidOperation

import requests
from django.urls import reverse

# =========================
#  Config & constantes
# =========================
API_URL   = os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com")
API_KEY   = os.getenv("CINETPAY_API_KEY")
SITE_ID   = os.getenv("CINETPAY_SITE_ID")

# Ces deux-là peuvent contenir des placeholders en dev ; on les filtrera.
RETURN_URL_ENV = os.getenv("CINETPAY_RETURN_URL")
NOTIFY_URL_ENV = os.getenv("CINETPAY_NOTIFY_URL")

ENV_MODE  = os.getenv("CINETPAY_ENV", "sandbox").lower()   # "sandbox" | "production"
CHANNELS  = os.getenv("CINETPAY_CHANNELS", "CREDIT_CARD")  # "ALL", "CREDIT_CARD", etc.

logger = logging.getLogger("cinetpay")


class CinetPayError(Exception):
    """Erreur applicative lisible pour les appels CinetPay."""
    pass


# =========================
#  Utils
# =========================
def _is_placeholder_url(url: str) -> bool:
    """Détecte un placeholder du style '<ton-ngrok-ici>' dans l'URL .env."""
    if not url:
        return True
    return "<" in url or ">" in url or "ton-ngrok-ici" in url


def _runtime_urls(request):
    """
    Fait un choix robuste pour return/notify :
    - Si .env fournit une URL réelle → on l'utilise.
    - Sinon → fallback dynamique basé sur host courant.
    """
    base = f"{request.scheme}://{request.get_host()}"

    return_url = (
        RETURN_URL_ENV
        if not _is_placeholder_url(RETURN_URL_ENV)
        else base + reverse("payment_return")
    )
    notify_url = (
        NOTIFY_URL_ENV
        if not _is_placeholder_url(NOTIFY_URL_ENV)
        else base + reverse("payment_notify")
    )

    return return_url, notify_url


def _amount_to_int(value) -> int:
    """
    CinetPay exige un ENTIER pour 'amount'.
    Accepte int/float/str/Decimal et convertit proprement.
    Lève une CinetPayError si impossible.
    """
    if value is None:
        raise CinetPayError("Montant manquant (amount None).")

    # Déjà un entier
    if isinstance(value, int):
        if value <= 0:
            raise CinetPayError("Le montant doit être > 0.")
        return value

    # Convertit via Decimal pour éviter les surprises de float
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError) as e:
        raise CinetPayError(f"Montant invalide: {value!r} ({e})")

    # Autoriser 15000, 15000.0, "15000", "15000.00" -> 15000
    if dec.as_tuple().exponent < 0:
        # Si des décimales existent, on refuse ou on arrondit ?
        # Ici on tronque vers l'entier (comportement sûr pour XOF sans centimes).
        dec = dec.to_integral_value(rounding="ROUND_DOWN")

    ivalue = int(dec)
    if ivalue <= 0:
        raise CinetPayError("Le montant doit être > 0.")
    return ivalue


def _post(path: str, json_payload: dict, timeout: int = 25) -> dict:
    """POST JSON avec gestion d’erreurs lisibles."""
    url = f"{API_URL.rstrip('/')}{path}"
    headers = {"Content-Type": "application/json"}

    try:
        r = requests.post(url, json=json_payload, headers=headers, timeout=timeout)
    except requests.RequestException as e:
        logger.error(f"[CinetPay][_post] HTTP error: {e}")
        raise CinetPayError(f"Erreur réseau vers CinetPay: {e}")

    # On veut toujours renvoyer une erreur lisible côté app
    try:
        data = r.json()
    except Exception:
        logger.error(f"[CinetPay][_post] Non-JSON response (status={r.status_code})")
        raise CinetPayError(f"Réponse non-JSON ({r.status_code})")

    if r.status_code >= 400:
        logger.error(f"[CinetPay][_post] HTTP {r.status_code}: {data}")
        raise CinetPayError({"http_status": r.status_code, "body": data})

    return data


# =========================
#  API Bas Niveau
# =========================
def init_payment(
    *,
    transaction_id: str,
    amount,  # accepte int/float/str/Decimal → sera converti en int
    currency: str = "XOF",
    description: str,
    channels: str | None = None,
    customer: dict | None = None,
    return_url: str | None = None,
    notify_url: str | None = None,
    metadata: dict | str | None = None,
) -> str:
    """
    Crée une transaction CinetPay et renvoie l'URL de paiement.
    - Ajoute return_url/notify_url si fournis (ou si disponibles via .env).
    - Force 'amount' en ENTIER, comme exigé par CinetPay (évite l'erreur 'amount must be an integer').
    """
    if not API_KEY or not SITE_ID:
        raise CinetPayError("CINETPAY_API_KEY / CINETPAY_SITE_ID manquants dans l'environnement.")

    amount_int = _amount_to_int(amount)

    # Certains intégrateurs exigent "metadata" stringifiée ; ici on passe tel quel si str,
    # sinon on passe l'objet (dict) et on laisse CinetPay accepter/ignorer.
    payload = {
        "apikey": API_KEY,
        "site_id": SITE_ID,
        "transaction_id": str(transaction_id),
        "amount": amount_int,                 # <-- ENTIER obligé !
        "currency": currency,
        "description": description,
        "channels": (channels or CHANNELS),
        "lang": "fr",
        "metadata": metadata if (metadata is not None) else {},
        # "env": ENV_MODE,  # À activer uniquement si votre console l'exige
    }

    # URLs de retour/notification
    if return_url:
        payload["return_url"] = return_url
    elif RETURN_URL_ENV and not _is_placeholder_url(RETURN_URL_ENV):
        payload["return_url"] = RETURN_URL_ENV

    if notify_url:
        payload["notify_url"] = notify_url
    elif NOTIFY_URL_ENV and not _is_placeholder_url(NOTIFY_URL_ENV):
        payload["notify_url"] = NOTIFY_URL_ENV

    # Données client (optionnelles)
    if customer:
        phone = customer.get("phone") or customer.get("phone_number") or ""
        payload.update({
            "customer_id": customer.get("id") or "",
            "customer_name": customer.get("name") or "",
            "customer_surname": customer.get("surname") or "",
            "customer_email": customer.get("email") or "",
            "customer_phone_number": phone,
            "customer_address": customer.get("address") or "",
            "customer_city": customer.get("city") or "",
            "customer_country": customer.get("country") or "",
            "customer_state": customer.get("state", "") or "",
            "customer_zip_code": customer.get("zip", "00000") or "00000",
        })

    logger.info(
        "[CinetPay][init] tx=%s amount=%s %s channels=%s",
        transaction_id,
        amount_int,
        currency,
        payload["channels"],
    )

    data = _post("/v2/payment", payload)

    # D'après la doc V2, code "201" = création OK
    code = str(data.get("code", ""))
    if code != "201":
        logger.error(f"[CinetPay][init] Unexpected code: {code} | response={data}")
        raise CinetPayError({"step": "init", "response": data})

    data_dict = data.get("data") or {}
    payment_url = data_dict.get("payment_url") or data_dict.get("checkout_url")
    if not payment_url:
        logger.error(
            "[CinetPay][init] payment_url manquant | response=%s",
            data,
        )
        raise CinetPayError({"step": "init", "error": "payment_url manquant", "response": data})

    return payment_url


def check_transaction(transaction_id: str) -> dict:
    """Vérifie l'état d'une transaction CinetPay (serveur à serveur)."""
    if not API_KEY or not SITE_ID:
        raise CinetPayError("CINETPAY_API_KEY / CINETPAY_SITE_ID manquants dans l'environnement.")

    payload = {"transaction_id": str(transaction_id), "site_id": SITE_ID, "apikey": API_KEY}
    logger.info(f"[CinetPay][check] tx={transaction_id}")
    return _post("/v2/payment/check", payload)


# =========================
#  Helpers Haut Niveau
# =========================
def init_payment_auto(order, request) -> str:
    """
    Construit l'init de paiement à partir d'un Order et renvoie l'URL de redirection.
    - Utilise amount_fcfa & currency du modèle.
    - Choisit des URLs return/notify robustes (env > fallback dynamique).
    """
    # Choix des URLs (si .env contient un placeholder, on fallback sur l'URL du site courant)
    return_url, notify_url = _runtime_urls(request)

    designation = f"{order.product.title} — {order.email}"
    tx = order.provider_ref or order.cinetpay_payment_id

    # order.amount_fcfa peut être int/Decimal/str → on laisse la fonction bas niveau sécuriser
    amount = order.amount_fcfa
    currency = (order.currency or "XOF").upper()

    # Appel bas niveau (accepte désormais return_url/notify_url)
    pay_url = init_payment(
        transaction_id=tx,
        amount=amount,  # <-- conversion en ENTIER faite dans init_payment via _amount_to_int
        currency=currency,
        description=designation,
        channels="ALL",  # ou CHANNELS selon ta stratégie
        customer={"email": order.email},
        return_url=return_url,
        notify_url=notify_url,
        metadata=(
            json.dumps({"tier_id": order.tier_id})
            if getattr(order, "tier_id", None)
            else None
        ),
    )

    logger.info(
        "[CinetPay][init_auto] order_id=%s tx=%s → redirect=%s",
        order.id,
        tx,
        pay_url,
    )
    return pay_url


def safe_check(transaction_id: str) -> dict:
    """
    En dev (clé/site non configurés), renvoie un statut 'ACCEPTED' pour faciliter les tests.
    En prod, fait le vrai check.
    """
    if not (API_KEY and SITE_ID):
        logger.warning(
            "[CinetPay][safe_check] API_KEY/SITE_ID manquants → renvoi mock ACCEPTED (dev)."
        )
        return {"code": "00", "data": {"status": "ACCEPTED"}}

    try:
        return check_transaction(transaction_id)
    except CinetPayError as e:
        logger.error("[CinetPay][safe_check] error=%s", e)
        raise
