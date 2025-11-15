# store/services/orange_money.py
"""
Service Orange Money pour les paiements Kit Complet.
"""
import hashlib
import hmac
import json
import logging
import os
from typing import Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# Configuration depuis les variables d'environnement
OM_API_URL = os.getenv("OM_API_URL", "https://api.orange.com/orange-money-webpay/ml/v1")
OM_MERCHANT_KEY = os.getenv("OM_MERCHANT_KEY")
OM_MERCHANT_ID = os.getenv("OM_MERCHANT_ID")
OM_CLIENT_ID = os.getenv("OM_CLIENT_ID")
OM_CLIENT_SECRET = os.getenv("OM_CLIENT_SECRET")
OM_WEBHOOK_SECRET = os.getenv("OM_WEBHOOK_SECRET", OM_MERCHANT_KEY)
OM_OAUTH_URL = os.getenv("OM_OAUTH_URL", "https://api.orange.com/oauth/v2/token")


class OrangeMoneyError(Exception):
    """Erreur applicative lisible pour les appels Orange Money."""

    pass


def get_oauth_token() -> Optional[str]:
    """
    Obtient un token OAuth 2.0 pour l'API Orange Money.
    
    Returns:
        Token d'accès ou None si échec
    """
    if not OM_CLIENT_ID or not OM_CLIENT_SECRET:
        logger.warning("[OM][get_oauth_token] OM_CLIENT_ID ou OM_CLIENT_SECRET manquants")
        return None
    
    try:
        response = requests.post(
            OM_OAUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": OM_CLIENT_ID,
                "client_secret": OM_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            logger.error(f"[OM][get_oauth_token] HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"[OM][get_oauth_token] Erreur: {e}")
        return None


def create_checkout(inquiry_id: int, amount: int, currency: str = "XOF", request=None) -> Tuple[str, str]:
    """
    Crée une session de paiement Orange Money.
    
    Args:
        inquiry_id: ID de l'inquiry
        amount: Montant en XOF
        currency: Devise (par défaut XOF)
        request: Objet request Django (pour construire les URLs)
    
    Returns:
        Tuple (redirect_url, external_ref)
    
    Raises:
        OrangeMoneyError: Si la création échoue
    """
    # Vérifier les credentials
    if not OM_MERCHANT_KEY or not OM_MERCHANT_ID:
        error_msg = "OM_MERCHANT_KEY / OM_MERCHANT_ID manquants dans l'environnement. Vérifiez votre fichier .env"
        logger.error(f"[OM][create_checkout] {error_msg}")
        raise OrangeMoneyError(error_msg)
    
    # Obtenir un token OAuth si nécessaire
    access_token = None
    if OM_CLIENT_ID and OM_CLIENT_SECRET:
        access_token = get_oauth_token()
        if not access_token:
            logger.warning("[OM][create_checkout] Impossible d'obtenir le token OAuth, tentative sans token")

    # Générer une référence transaction unique
    import uuid
    external_ref = f"OM-{uuid.uuid4().hex[:16].upper()}"
    
    # Construire les URLs de retour
    if request:
        base_url = f"{request.scheme}://{request.get_host()}"
        return_url = f"{base_url}/payments/om/return/"
        notify_url = f"{base_url}/payments/om/notify/"
    else:
        return_url = os.getenv("OM_RETURN_URL", "")
        notify_url = os.getenv("OM_NOTIFY_URL", "")

    # Payload pour Orange Money (structure simplifiée, à adapter selon leur API réelle)
    payload = {
        "merchant_key": OM_MERCHANT_KEY,
        "merchant_id": OM_MERCHANT_ID,
        "transaction_id": external_ref,
        "amount": amount,
        "currency": currency,
        "return_url": return_url,
        "notify_url": notify_url,
        "description": f"Kit Complet - Inquiry #{inquiry_id}",
    }

    try:
        # Préparer les headers avec le token OAuth si disponible
        headers = {"Content-Type": "application/json"}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        # TODO: Adapter l'endpoint selon la documentation réelle Orange Money
        # Pour l'instant, on simule une structure similaire à CinetPay
        # Note: L'endpoint réel peut être différent selon la documentation Orange Money
        logger.info(f"[OM][create_checkout] Appel API: {OM_API_URL}/webpay/init")
        response = requests.post(
            f"{OM_API_URL}/webpay/init",
            json=payload,
            headers=headers,
            timeout=25,
        )
        
        if response.status_code >= 400:
            logger.error(f"[OM][create_checkout] HTTP {response.status_code}: {response.text}")
            raise OrangeMoneyError(f"Erreur Orange Money: {response.status_code}")
        
        data = response.json()
        
        # Structure attendue (à adapter selon la vraie API)
        payment_url = data.get("payment_url") or data.get("checkout_url") or data.get("url")
        if not payment_url:
            logger.error(f"[OM][create_checkout] payment_url manquant: {data}")
            raise OrangeMoneyError("payment_url manquant dans la réponse Orange Money")
        
        logger.info(f"[OM][create_checkout] inquiry_id={inquiry_id} tx={external_ref} → {payment_url}")
        return payment_url, external_ref
        
    except requests.RequestException as e:
        logger.error(f"[OM][create_checkout] Erreur réseau: {e}")
        raise OrangeMoneyError(f"Erreur réseau vers Orange Money: {e}")


def verify_webhook(request) -> Optional[dict]:
    """
    Vérifie la signature du webhook Orange Money et retourne le payload validé.
    
    Args:
        request: Objet request Django
    
    Returns:
        dict avec le payload validé ou None si invalide
    """
    if not OM_WEBHOOK_SECRET:
        logger.warning("[OM][verify_webhook] OM_WEBHOOK_SECRET manquant")
        return None

    # Récupérer la signature depuis les headers
    signature = (
        request.headers.get("X-Signature")
        or request.headers.get("X-OM-Signature")
        or request.META.get("HTTP_X_SIGNATURE")
        or request.META.get("HTTP_X_OM_SIGNATURE")
    )

    if not signature:
        logger.warning("[OM][verify_webhook] Signature manquante")
        return None

    # Vérifier la signature HMAC
    raw_body = request.body or b""
    expected_digest = hmac.new(
        OM_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_digest):
        logger.warning("[OM][verify_webhook] Signature invalide")
        return None

    try:
        payload = json.loads(raw_body.decode("utf-8"))
        return payload
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"[OM][verify_webhook] Erreur parsing JSON: {e}")
        return None


def map_provider_status_to_paid(provider_status: str) -> bool:
    """
    Mappe le statut du provider vers PAID/FAILED.
    
    Args:
        provider_status: Statut renvoyé par Orange Money
    
    Returns:
        True si payé, False sinon
    """
    paid_statuses = ["PAID", "SUCCESS", "COMPLETED", "ACCEPTED", "CONFIRMED"]
    return provider_status.upper() in paid_statuses


def check_transaction_status(external_ref: str) -> Tuple[bool, Optional[str]]:
    """
    Vérifie le statut d'une transaction Orange Money (serveur à serveur).
    
    Args:
        external_ref: Référence de la transaction
    
    Returns:
        Tuple (is_paid, provider_tx_id ou None)
    """
    if not OM_MERCHANT_KEY or not OM_MERCHANT_ID:
        logger.warning("[OM][check_transaction] Clés manquantes → mock PAID (dev)")
        return True, external_ref

    try:
        # TODO: Adapter selon la vraie API Orange Money
        response = requests.post(
            f"{OM_API_URL}/webpay/check",
            json={
                "merchant_key": OM_MERCHANT_KEY,
                "merchant_id": OM_MERCHANT_ID,
                "transaction_id": external_ref,
            },
            timeout=25,
        )

        if response.status_code >= 400:
            logger.error(f"[OM][check_transaction] HTTP {response.status_code}")
            return False, None

        data = response.json()
        status = data.get("status", "").upper()
        provider_tx_id = data.get("transaction_id") or external_ref

        if map_provider_status_to_paid(status):
            return True, provider_tx_id

        return False, provider_tx_id

    except requests.RequestException as e:
        logger.error(f"[OM][check_transaction] Erreur: {e}")
        return False, None
        
# ---- STUBS SANDBOX LOCAUX ----
import os as _os, random as _random, uuid as _uuid

def _mock_response(payload):
    if _os.getenv("OM_SANDBOX_MOCK", "0") == "1":
        fake_url = f"https://sandbox.orange-money.fake/checkout/{payload['transaction_id']}"
        return {"payment_url": fake_url, "transaction_id": payload["transaction_id"]}
    return None

# Sauvegarder les vraies références des fonctions si elles existent déjà
try:
    _REAL_create_checkout = create_checkout
    _REAL_check_transaction_status = check_transaction_status
except NameError:
    _REAL_create_checkout = None
    _REAL_check_transaction_status = None

def create_checkout(inquiry_id: int, amount: int, currency: str = "XOF", request=None):
    # Sandbox forcé si OM_SANDBOX_MOCK=1 OU si credentials manquants (dev)
    if _os.getenv("OM_SANDBOX_MOCK", "0") == "1" or (not OM_MERCHANT_KEY or not OM_MERCHANT_ID):
        tx = f"OM-SBX-{_uuid.uuid4().hex[:10].upper()}"
        # En mock, rediriger vers une page locale simulant le checkout
        if request is not None:
            base_url = f"{request.scheme}://{request.get_host()}"
            mock_url = f"{base_url}/payments/om/mock/?transaction_id={tx}"
            return mock_url, tx
        # Fallback: simuler retour immédiat succès si request absent
        return_url = _os.getenv("OM_RETURN_URL") or ""
        if return_url:
            return f"{return_url}?transaction_id={tx}", tx
        return f"/payments/om/return/?transaction_id={tx}", tx
    if _REAL_create_checkout:
        return _REAL_create_checkout(inquiry_id, amount, currency, request)
    raise RuntimeError("create_checkout non défini")

def check_transaction_status(external_ref: str):
    # Sandbox forcé si OM_SANDBOX_MOCK=1 OU si credentials manquants (dev)
    if _os.getenv("OM_SANDBOX_MOCK", "0") == "1" or (not OM_MERCHANT_KEY or not OM_MERCHANT_ID):
        paid = _random.choice([True, True, False])
        return paid, external_ref
    if _REAL_check_transaction_status:
        return _REAL_check_transaction_status(external_ref)
    return False, None