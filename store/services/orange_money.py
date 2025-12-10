# store/services/orange_money.py
"""
Service Orange Money WebPay Dev (Mali, Sandbox) pour AuditShield.
Implémentation basée sur le guide officiel Orange Money WebPay Dev.
"""
import base64
import json
import logging
import os
from typing import Dict, Any, Optional

import requests
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def _mask_sensitive_data(data: dict, keys_to_mask: list = None) -> dict:
    """
    Masque les données sensibles dans un dict pour le logging.
    
    Args:
        data: Dictionnaire à masquer
        keys_to_mask: Liste des clés à masquer (défaut: token, secret, key, password)
    
    Returns:
        Copie du dict avec les valeurs sensibles masquées
    """
    if keys_to_mask is None:
        keys_to_mask = ["token", "secret", "key", "password", "auth"]
    
    # Clés à ne jamais masquer (whitelist)
    never_mask = ["token_type", "grant_type", "status", "message", "currency", 
                  "order_id", "amount", "lang", "reference"]
    
    masked = data.copy()
    for key, value in masked.items():
        # Ne jamais masquer les clés whitelistées
        if key in never_mask:
            continue
            
        if isinstance(value, dict):
            masked[key] = _mask_sensitive_data(value, keys_to_mask)
        elif isinstance(value, str):
            # Masquer si la clé contient un mot sensible (mais pas dans la whitelist)
            if any(sensitive in key.lower() for sensitive in keys_to_mask):
                # Garder les 4 premiers caractères pour debug
                masked[key] = f"{value[:4]}***masked***" if len(value) > 4 else "***masked***"
    return masked


def _mask_authorization_header(headers: dict) -> dict:
    """
    Masque le header Authorization pour le logging.
    
    Args:
        headers: Dict des headers HTTP
    
    Returns:
        Copie des headers avec Authorization masqué
    """
    masked = headers.copy()
    if "Authorization" in masked:
        auth_value = masked["Authorization"]
        # Extraire le type (Bearer, Basic, etc.) et masquer le token
        parts = auth_value.split(" ", 1)
        if len(parts) == 2:
            auth_type, token = parts
            masked["Authorization"] = f"{auth_type} ***masked***"
        else:
            masked["Authorization"] = "***masked***"
    return masked

# Cache pour le token OAuth (durée de vie ~90 jours selon guide)
_TOKEN_CACHE_KEY = "orange_money_access_token"
_TOKEN_CACHE_TIMEOUT = 90 * 24 * 60 * 60  # 90 jours en secondes


class OrangeMoneyError(Exception):
    """Erreur applicative lisible pour les appels Orange Money."""
    pass


class OrangeMoneyAuthError(OrangeMoneyError):
    """Erreur d'authentification OAuth Orange Money."""
    pass


class OrangeMoneyAPIError(OrangeMoneyError):
    """Erreur lors d'un appel API Orange Money."""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


def _get_config() -> Dict[str, str]:
    """
    Récupère la configuration Orange Money depuis Django settings.
    Lève ImproperlyConfigured si les variables essentielles manquent.
    
    Conforme au guide officiel Orange Money WebPay Dev.
    """
    from django.conf import settings
    
    config = {
        # OAuth & API
        "CLIENT_ID": getattr(settings, "ORANGE_CLIENT_ID", ""),
        "CLIENT_SECRET": getattr(settings, "ORANGE_CLIENT_SECRET", ""),
        "APPLICATION_ID": getattr(settings, "ORANGE_APPLICATION_ID", ""),
        
        # URLs API
        "OAUTH_URL": getattr(settings, "ORANGE_OAUTH_TOKEN_URL", "https://api.orange.com/oauth/v3/token"),
        "WEBPAY_URL": getattr(settings, "ORANGE_WEBPAY_DEV_URL", "https://api.orange.com/orange-money-webpay/dev/v1/webpayment"),
        "TRANSACTION_STATUS_URL": getattr(settings, "ORANGE_TRANSACTION_STATUS_URL", "https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus"),
        
        # Merchant
        "MERCHANT_KEY": getattr(settings, "ORANGE_MERCHANT_KEY", ""),
        "MERCHANT_MSISDN": getattr(settings, "ORANGE_MERCHANT_MSISDN", ""),
        "AGENT_CODE": getattr(settings, "ORANGE_MERCHANT_AGENT_CODE", ""),
        
        # Callback URLs
        "RETURN_URL": getattr(settings, "ORANGE_RETURN_URL", "http://127.0.0.1:8000/payments/om/return/"),
        "CANCEL_URL": getattr(settings, "ORANGE_CANCEL_URL", "http://127.0.0.1:8000/payments/om/return/"),
        "NOTIFY_URL": getattr(settings, "ORANGE_NOTIFY_URL", "http://127.0.0.1:8000/payments/om/notify/"),
        
        # Test/Sandbox
        "TEST_SUBSCRIBER_MSISDN": getattr(settings, "ORANGE_TEST_SUBSCRIBER_MSISDN", "77011011234"),
        "TEST_SUBSCRIBER_PIN": getattr(settings, "ORANGE_TEST_SUBSCRIBER_PIN", "4940"),
        
        # Code pays (ml = Mali, ow = Guinée, ci = Côte d'Ivoire, etc.)
        "COUNTRY_CODE": getattr(settings, "ORANGE_COUNTRY_CODE", "ml"),
    }
    
    # Validation des variables essentielles
    required = ["CLIENT_ID", "CLIENT_SECRET", "MERCHANT_KEY"]
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise ImproperlyConfigured(
            f"Orange Money: variables manquantes dans .env: {', '.join(missing)}"
        )
    
    return config


def get_access_token() -> str:
    """
    Obtient un access_token OAuth depuis Orange Money.
    
    Le token est mis en cache et réutilisé jusqu'à expiration (durée de vie ~90 jours selon guide).
    
    Endpoint: POST https://api.orange.com/oauth/v2/token
    
    Headers:
        Authorization: Basic base64(<client_id>:<client_secret>)
        Content-Type: application/x-www-form-urlencoded
    
    Body:
        grant_type=client_credentials
    
    Returns:
        str: Access token pour les appels API suivants
    
    Raises:
        OrangeMoneyAuthError: Si l'authentification échoue
        OrangeMoneyConfigurationError: Si la configuration est manquante
    """
    # Vérifier le cache d'abord
    cached_token = cache.get(_TOKEN_CACHE_KEY)
    if cached_token:
        logger.debug("[OM][OAuth] Token récupéré depuis le cache")
        return cached_token
    
    config = _get_config()
    
    client_id = config["CLIENT_ID"]
    client_secret = config["CLIENT_SECRET"]
    oauth_url = config["OAUTH_URL"]
    
    # Auth Basic avec client_id:client_secret
    credentials = f"{client_id}:{client_secret}"
    auth_header = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    
    # Payload pour grant_type=client_credentials
    data = {
        "grant_type": "client_credentials",
    }
    
    try:
        # === LOGGING DÉTAILLÉ DE LA REQUÊTE ===
        masked_headers = _mask_authorization_header(headers)
        logger.info(
            f"ORANGE_WEBPAY_REQUEST | OAuth Token | "
            f"url={oauth_url} | "
            f"headers={json.dumps(masked_headers)} | "
            f"body={json.dumps(data)}"
        )
        
        response = requests.post(
            oauth_url,
            data=data,
            headers=headers,
            timeout=30,
        )
        
        # === LOGGING DÉTAILLÉ DE LA RÉPONSE ===
        try:
            response_json = response.json()
            # Masquer les données sensibles dans la réponse (access_token)
            masked_response = _mask_sensitive_data(response_json, ["token"])
            logger.info(
                f"ORANGE_WEBPAY_RESPONSE | OAuth Token | "
                f"status={response.status_code} | "
                f"body={json.dumps(masked_response, ensure_ascii=False)}"
            )
        except json.JSONDecodeError:
            logger.info(
                f"ORANGE_WEBPAY_RESPONSE | OAuth Token | "
                f"status={response.status_code} | "
                f"body={response.text}"
            )
        
        if response.status_code != 200:
            logger.error(
                f"[OM][OAuth] HTTP {response.status_code}: {response.text}"
            )
            raise OrangeMoneyAuthError(
                f"Erreur OAuth {response.status_code}: {response.text}"
            )
        
        result = response.json()
        access_token = result.get("access_token")
        expires_in = result.get("expires_in", _TOKEN_CACHE_TIMEOUT)
        
        if not access_token:
            logger.error(f"[OM][OAuth] Pas d'access_token dans la réponse: {result}")
            raise OrangeMoneyAuthError("Access token manquant dans la réponse OAuth")
        
        # Mettre en cache le token (utiliser expires_in si fourni, sinon 90 jours)
        cache_timeout = min(expires_in - 3600, _TOKEN_CACHE_TIMEOUT)  # Expirer 1h avant la vraie expiration
        cache.set(_TOKEN_CACHE_KEY, access_token, cache_timeout)
        
        logger.info(f"[OM][OAuth] Token obtenu avec succès (cache pour {cache_timeout}s)")
        return access_token
        
    except requests.RequestException as e:
        logger.error(f"[OM][OAuth] Erreur réseau: {e}", exc_info=True)
        raise OrangeMoneyAuthError(f"Erreur réseau lors de l'authentification: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"[OM][OAuth] Réponse non-JSON: {e}")
        raise OrangeMoneyAuthError(f"Réponse invalide de l'API OAuth: {e}")


def create_payment_request(payment, request=None) -> Dict[str, Any]:
    """
    Crée une demande de paiement Orange Money WebPay Dev.
    
    Endpoint: POST https://api.orange.com/orange-money-webpay/dev/v1/webpayment
    
    Headers:
        Authorization: Bearer <access_token>
        Content-Type: application/json
    
    Payload (selon PDF):
    {
        "merchant_key": "<OM_MERCHANT_KEY>",
        "currency": "XOF",
        "order_id": "<payment.uuid>",
        "amount": <payment.amount_fcfa>,
        "return_url": "<OM_RETURN_URL>",
        "cancel_url": "<OM_RETURN_URL>",
        "notif_url": "<OM_NOTIFY_URL>",
        "lang": "fr",
        "reference": "AuditShield"
    }
    
    Args:
        payment: Instance du modèle Payment ou Order Django
    
    Returns:
        Dict contenant:
        - payment_url: URL de redirection vers Orange Money
        - pay_token: Token de paiement (optionnel)
        - order_id: ID de la commande
        - raw_response: Réponse complète de l'API
    
    Raises:
        OrangeMoneyAPIError: Si l'appel API échoue
    """
    if payment is None:
        # Sécurité défensive : éviter un crash si payment est None
        # Exemple courant en shell : Payment.objects.first() peut retourner None
        raise OrangeMoneyAPIError(
            "Instance de paiement manquante (payment=None). "
            "Passe un Order ou Payment valide à create_payment_request()."
        )

    config = _get_config()
    
    # Obtenir l'access token
    try:
        access_token = get_access_token()
    except OrangeMoneyAuthError as e:
        logger.error(f"[OM][create_payment] Erreur OAuth: {e}")
        raise
    
    # Construire le payload selon le PDF
    # Utiliser payment.uuid comme order_id (limité à 30 chars selon le guide)
    # Gestion robuste si 'uuid' n'existe pas (ex: modèle Payment legacy)
    if hasattr(payment, "uuid") and getattr(payment, "uuid"):
        order_uuid = str(payment.uuid)
    elif hasattr(payment, "order_id") and getattr(payment, "order_id"):
        # Pour le modèle Payment(store.models.Payment)
        order_uuid = str(payment.order_id)
    else:
        # Fallback sur la PK numérique
        order_uuid = str(payment.id)
    # Tronquer order_id à 30 caractères max (selon guide)
    order_id = order_uuid[:30]
    amount = int(getattr(payment, "amount_fcfa", getattr(payment, "amount", 0)))
    
    # IMPORTANT: En mode DEV/Sandbox, utiliser "OUV" comme currency (selon guide)
    # En production, utiliser la devise du pays (XOF pour Mali)
    currency = "OUV"  # Devise sandbox selon guide Orange Money
    
    # Construire les URLs de retour dynamiquement si nécessaire
    # Orange Money n'accepte pas localhost/127.0.0.1, donc on doit utiliser une URL publique
    return_url = config["RETURN_URL"]
    notify_url = config["NOTIFY_URL"]
    
    # Vérifier si les URLs contiennent localhost/127.0.0.1 (Orange Money les rejette)
    has_localhost = ("localhost" in return_url.lower() or "127.0.0.1" in return_url.lower() or 
                     "localhost" in notify_url.lower() or "127.0.0.1" in notify_url.lower())
    
    if has_localhost:
        # Vérifier si une URL publique de test est configurée (pour sandbox)
        # Selon le guide Orange Money, on peut utiliser des URLs de test publiques
        # En mode sandbox, on peut utiliser n'importe quelle URL publique valide
        test_public_url = os.getenv("OM_TEST_PUBLIC_URL", "").strip()
        ngrok_url = os.getenv("OM_NGROK_URL", "").strip()
        
        # Si aucune URL n'est configurée, utiliser une URL de test par défaut pour le sandbox
        # (comme dans les exemples du guide Orange Money)
        if not test_public_url and not ngrok_url:
            # Utiliser une URL de test par défaut pour le sandbox (comme dans guide_orange.md)
            # Cette URL n'a pas besoin de pointer vers notre serveur, c'est juste pour que l'API accepte
            test_public_url = "http://myvirtualshop.webnode.es"  # Exemple du guide Orange Money
            logger.warning(
                "[OM][create_payment] Aucune URL publique configurée. "
                f"Utilisation d'une URL de test par défaut pour le sandbox: {test_public_url}"
            )
        
        if test_public_url:
            # Utiliser l'URL publique de test pour construire les URLs
            from django.urls import reverse
            base = test_public_url.rstrip("/")
            return_url = base + reverse("store:orange_return")
            
            # Pour notify_url, utiliser ngrok si disponible (pour recevoir les webhooks en local)
            # Sinon utiliser la même URL publique de test
            if ngrok_url:
                notify_base = ngrok_url.rstrip("/")
                notify_url = notify_base + reverse("store:orange_notify")
                logger.info(f"[OM][create_payment] Using test public URL for return: {return_url}")
                logger.info(f"[OM][create_payment] Using ngrok URL for notify (webhooks): {notify_url}")
            else:
                notify_url = base + reverse("store:orange_notify")
                logger.info(f"[OM][create_payment] Using test public URL (sandbox): return={return_url}, notify={notify_url}")
                logger.warning(
                    "[OM][create_payment] Note: notify_url utilise une URL de test. "
                    "Les webhooks ne seront pas reçus en local. "
                    "Configurez OM_NGROK_URL pour recevoir les webhooks."
                )
        elif ngrok_url:
            # Fallback sur ngrok si pas d'URL publique de test
            from django.urls import reverse
            base = ngrok_url.rstrip("/")
            return_url = base + reverse("store:orange_return")
            notify_url = base + reverse("store:orange_notify")
            logger.info(f"[OM][create_payment] Using ngrok URLs: return={return_url}, notify={notify_url}")
    
    payload = {
        "merchant_key": config["MERCHANT_KEY"],
        "currency": currency,
        "order_id": order_id,
        "amount": amount,
        "return_url": return_url,
        "cancel_url": return_url,  # Même URL pour cancel
        "notif_url": notify_url,
        "lang": "fr",
        "reference": "AuditShield",  # Limité à 30 chars selon guide
    }
    
    # Ajouter applicationId si configuré (certaines versions de l'API le requièrent)
    if config.get("APPLICATION_ID"):
        payload["applicationId"] = config["APPLICATION_ID"]
        logger.info(f"[OM][create_payment] applicationId ajouté: {config['APPLICATION_ID']}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    webpay_url = config["WEBPAY_URL"]
    
    try:
        # === LOGGING DÉTAILLÉ DE LA REQUÊTE ===
        # Masquer merchant_key dans le payload pour le logging
        masked_payload = _mask_sensitive_data(payload, ["key"])
        masked_headers = _mask_authorization_header(headers)
        
        logger.info(
            f"ORANGE_WEBPAY_REQUEST | WebPayment Init | "
            f"url={webpay_url} | "
            f"headers={json.dumps(masked_headers)} | "
            f"body={json.dumps(masked_payload, ensure_ascii=False)}"
        )
        logger.info(
            f"[OM][create_payment] Initiating payment: order_id={order_id}, "
            f"amount={amount} XOF"
        )
        
        response = requests.post(
            webpay_url,
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        # === LOGGING DÉTAILLÉ DE LA RÉPONSE ===
        try:
            response_json = response.json()
            # Masquer les tokens sensibles (pay_token, notif_token)
            masked_response = _mask_sensitive_data(response_json, ["token"])
            logger.info(
                f"ORANGE_WEBPAY_RESPONSE | WebPayment Init | "
                f"status={response.status_code} | "
                f"body={json.dumps(masked_response, ensure_ascii=False, indent=2)}"
            )
        except json.JSONDecodeError:
            logger.info(
                f"ORANGE_WEBPAY_RESPONSE | WebPayment Init | "
                f"status={response.status_code} | "
                f"body={response.text}"
            )
        
        # Vérifier le status_code selon le guide (201 attendu pour succès)
        if response.status_code != 201:
            error_data = {}
            try:
                error_data = response.json()
            except Exception:
                error_data = {"error": response.text}
            
            logger.error(
                f"[OM][create_payment] HTTP {response.status_code} (attendu 201): {error_data}"
            )
            raise OrangeMoneyAPIError(
                f"Erreur API Orange Money {response.status_code} (attendu 201)",
                status_code=response.status_code,
                response_data=error_data,
            )
        
        result = response.json()
        
        # Log structuré de la réponse (sans données sensibles)
        logger.info(
            f"[OM][create_payment] Response status={response.status_code} | "
            f"status={result.get('status')} | message={result.get('message')}"
        )
        logger.debug(f"[OM][create_payment] Full API response: {json.dumps(result, indent=2)}")
        
        # Extraire les informations pertinentes selon le guide
        payment_url = result.get("payment_url") or result.get("pay_url")
        pay_token = result.get("pay_token") or result.get("token")
        notif_token = result.get("notif_token")
        
        if not pay_token:
            logger.error(f"[OM][create_payment] pay_token manquant dans la réponse: {result}")
            raise OrangeMoneyAPIError(
                "pay_token manquant dans la réponse Orange Money",
                response_data=result,
            )
        
        # IMPORTANT: Utiliser l'URL retournée par l'API Orange Money
        # L'API retourne déjà l'URL correcte selon le pays et l'environnement
        # Ne PAS reconstruire l'URL nous-mêmes car les domaines varient selon les pays
        if not payment_url:
            # Si l'API ne retourne pas d'URL, construire une URL de fallback
            # En mode sandbox (/dev/v1/), utiliser le domaine sandbox universel
            if "/dev/v1/webpayment" in webpay_url:
                # Sandbox: utiliser le domaine universel ow-sb (qui semble être partagé)
                payment_url = f"https://webpayment-ow-sb.orange-money.com/payment/pay_token/{pay_token}"
                logger.warning(
                    f"[OM][create_payment] payment_url manquant dans la réponse API | "
                    f"Utilisation de l'URL sandbox par défaut: {payment_url}"
                )
            else:
                # Production: erreur si pas d'URL
                logger.error(f"[OM][create_payment] payment_url manquant dans la réponse: {result}")
                raise OrangeMoneyAPIError(
                    "payment_url manquant dans la réponse Orange Money",
                    response_data=result,
                )
        
        # Log de l'URL finale
        logger.info(
            f"[OM][create_payment] URL de paiement: {payment_url} | "
            f"Source: {'API response' if result.get('payment_url') else 'Fallback'}"
        )
        
        logger.info(
            f"[OM][create_payment] Payment créé avec succès | "
            f"payment_url={payment_url} | pay_token={pay_token[:20]}... | "
            f"notif_token={notif_token[:20] if notif_token else 'N/A'}..."
        )
        
        return {
            "payment_url": payment_url,
            "pay_token": pay_token,
            "notif_token": notif_token,
            "order_id": order_id,
            "raw_response": result,
        }
        
    except requests.RequestException as e:
        logger.error(f"[OM][create_payment] Erreur réseau: {e}", exc_info=True)
        raise OrangeMoneyAPIError(f"Erreur réseau lors de la création du paiement: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"[OM][create_payment] Réponse non-JSON: {e}")
        raise OrangeMoneyAPIError(f"Réponse invalide de l'API: {e}")


def check_transaction_status(order_id: str, amount: Optional[int] = None, pay_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Vérifie le statut d'une transaction Orange Money.
    
    Endpoint: POST https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus
    
    Selon le guide (section 4), le payload doit contenir:
    - order_id (obligatoire)
    - amount (recommandé)
    - pay_token (recommandé)
    
    Args:
        order_id: ID de la commande (order_id utilisé lors de la création)
        amount: Montant de la transaction (optionnel mais recommandé)
        pay_token: Token de paiement retourné lors de la création (optionnel mais recommandé)
    
    Returns:
        Dict contenant le statut de la transaction:
        - status: Statut de la transaction (INITIATED, PENDING, EXPIRED, SUCCESS, FAILED)
        - order_id: ID de la commande
        - txnid: ID de transaction Orange Money (si disponible)
        - raw_response: Réponse complète de l'API
    """
    config = _get_config()
    
    # Obtenir l'access token
    try:
        access_token = get_access_token()
    except OrangeMoneyAuthError as e:
        logger.error(f"[OM][check_status] Erreur OAuth: {e}")
        return {"status": "ERROR", "error": str(e)}
    
    # Construire le payload selon le guide (section 4)
    payload = {
        "merchant_key": config["MERCHANT_KEY"],
        "order_id": order_id,
    }
    
    # Ajouter amount et pay_token si fournis (recommandé par le guide)
    if amount is not None:
        payload["amount"] = amount
    if pay_token:
        payload["pay_token"] = pay_token
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    status_url = config["TRANSACTION_STATUS_URL"]
    
    try:
        # === LOGGING DÉTAILLÉ DE LA REQUÊTE ===
        masked_payload = _mask_sensitive_data(payload, ["key", "token"])
        masked_headers = _mask_authorization_header(headers)
        
        logger.info(
            f"ORANGE_WEBPAY_REQUEST | Transaction Status | "
            f"url={status_url} | "
            f"headers={json.dumps(masked_headers)} | "
            f"body={json.dumps(masked_payload, ensure_ascii=False)}"
        )
        logger.info(
            f"[OM][check_status] Checking status | order_id={order_id} | "
            f"amount={amount} | pay_token={pay_token[:20] if pay_token else 'N/A'}..."
        )
        
        response = requests.post(
            status_url,
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        # === LOGGING DÉTAILLÉ DE LA RÉPONSE ===
        try:
            response_json = response.json()
            logger.info(
                f"ORANGE_WEBPAY_RESPONSE | Transaction Status | "
                f"status={response.status_code} | "
                f"body={json.dumps(response_json, ensure_ascii=False, indent=2)}"
            )
        except json.JSONDecodeError:
            logger.info(
                f"ORANGE_WEBPAY_RESPONSE | Transaction Status | "
                f"status={response.status_code} | "
                f"body={response.text}"
            )
        
        if response.status_code != 201:
            logger.error(
                f"[OM][check_status] HTTP {response.status_code} (attendu 201): {response.text}"
            )
            return {
                "status": "ERROR",
                "error_message": f"Erreur API: {response.status_code}",
                "raw_response": response.text,
            }
        
        data = response.json()
        transaction_status = data.get("status", "UNKNOWN")
        txnid = data.get("txnid")
        
        logger.info(
            f"[OM][check_status] Status retrieved | order_id={order_id} | "
            f"status={transaction_status} | txnid={txnid}"
        )
        
        return {
            "status": transaction_status,
            "order_id": order_id,
            "txnid": txnid,
            "raw_response": data,
        }
        
    except requests.RequestException as e:
        logger.error(f"[OM][check_status] Erreur réseau: {e}", exc_info=True)
        return {
            "status": "ERROR",
            "error_message": f"Erreur réseau: {e}",
        }
    except json.JSONDecodeError as e:
        logger.error(f"[OM][check_status] Réponse non-JSON: {e}")
        return {
            "status": "ERROR",
            "error_message": f"Erreur parsing: {e}",
        }


def verify_webhook(request) -> Optional[Dict[str, Any]]:
    """
    Vérifie et parse le webhook Orange Money.
    
    Selon le guide (section 3.3), le webhook contient:
    - status: "SUCCESS" ou "FAILED"
    - notif_token: Token de notification (doit correspondre au notif_token retourné lors de la création)
    - txnid: ID de transaction Orange Money
    
    Args:
        request: Objet request Django
    
    Returns:
        dict avec le payload validé ou None si invalide
    """
    try:
        # Parser le payload JSON
        payload = json.loads(request.body.decode("utf-8"))
        logger.info(
            f"[OM][verify_webhook] Payload reçu | status={payload.get('status')} | "
            f"notif_token={payload.get('notif_token', 'N/A')[:20] if payload.get('notif_token') else 'N/A'}... | "
            f"txnid={payload.get('txnid', 'N/A')}"
        )
        logger.debug(f"[OM][verify_webhook] Full payload: {json.dumps(payload, indent=2)}")
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
    paid_statuses = ["PAID", "SUCCESS", "COMPLETED", "ACCEPTED", "CONFIRMED", "SUCCESSFUL"]
    return provider_status.upper() in paid_statuses


# === FONCTIONS DE COMPATIBILITÉ AVEC L'ANCIEN CODE ===

def create_checkout(inquiry_id: int, amount: int, currency: str = "XOF", request=None) -> tuple:
    """
    Fonction de compatibilité avec l'ancien code pour les Kit complets.
    """
    from store.models import ClientInquiry
    
    inquiry = ClientInquiry.objects.filter(pk=inquiry_id).first()
    if not inquiry:
        raise OrangeMoneyError(f"Inquiry {inquiry_id} introuvable")
    
    order = inquiry.order
    if not order:
        raise OrangeMoneyError(f"Aucune commande associée à l'inquiry {inquiry_id}")
    
    try:
        result = create_payment_request(order)
        return result["payment_url"], result["order_id"]
    except OrangeMoneyAPIError as e:
        logger.error(f"[OM][create_checkout] Erreur: {e}")
        raise


def check_transaction_status_legacy(external_ref: str) -> tuple:
    """
    Fonction de compatibilité avec l'ancien code.
    """
    result = check_transaction_status(external_ref)
    status = result.get("status", "")
    is_paid = map_provider_status_to_paid(status)
    return is_paid, external_ref
