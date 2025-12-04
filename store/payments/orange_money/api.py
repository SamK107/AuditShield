"""
Client API Orange Money Mali.
Gère l'authentification OAuth et l'initiation des paiements.
"""
import base64
import json
import logging
import os
from typing import Dict, Any, Optional
import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .exceptions import (
    OrangeMoneyAPIError,
    OrangeMoneyAuthError,
    OrangeMoneyConfigurationError,
)

logger = logging.getLogger(__name__)


def get_orange_money_config() -> Dict[str, Any]:
    """
    Récupère la configuration Orange Money depuis les settings Django.
    Lève ImproperlyConfigured si les variables essentielles manquent.
    """
    config = getattr(settings, "ORANGE_MONEY_CONFIG", None)
    if not config:
        # Vérifier les variables d'environnement directement
        client_id = os.getenv("OM_CLIENT_ID")
        client_secret = os.getenv("OM_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise ImproperlyConfigured(
                "Orange Money non configuré : OM_CLIENT_ID et OM_CLIENT_SECRET requis dans .env"
            )
        
        # Construire la config depuis les variables d'env
        config = {
            "CLIENT_ID": client_id,
            "CLIENT_SECRET": client_secret,
            "MERCHANT_ID": os.getenv("OM_MERCHANT_ID", ""),
            "MERCHANT_KEY": os.getenv("OM_MERCHANT_KEY", ""),
            "MSISDN_TEST": os.getenv("OM_MSISDN_TEST", "77011011234"),
            "API_BASE_URL": os.getenv("OM_API_BASE_URL", "https://api.orange.com"),
            "COLLECT_URL": os.getenv("OM_COLLECT_URL", ""),
            "CALLBACK_URL": os.getenv("OM_CALLBACK_URL", ""),
            "RETURN_URL_SUCCESS": os.getenv("OM_RETURN_URL_SUCCESS", ""),
            "RETURN_URL_FAILED": os.getenv("OM_RETURN_URL_FAILED", ""),
        }
    
    return config


def get_access_token() -> str:
    """
    Obtient un access_token OAuth depuis Orange Money.
    
    Returns:
        str: Access token pour les appels API suivants
    
    Raises:
        OrangeMoneyAuthError: Si l'authentification échoue
        OrangeMoneyConfigurationError: Si la configuration est manquante
    """
    config = get_orange_money_config()
    
    client_id = config.get("CLIENT_ID")
    client_secret = config.get("CLIENT_SECRET")
    api_base_url = config.get("API_BASE_URL", "https://api.orange.com")
    
    if not client_id or not client_secret:
        raise OrangeMoneyConfigurationError(
            "OM_CLIENT_ID et OM_CLIENT_SECRET requis dans .env"
        )
    
    # URL OAuth (standard Orange Money)
    oauth_url = f"{api_base_url.rstrip('/')}/oauth/v3/token"
    
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
        logger.info(f"[OM][OAuth] Requesting token from {oauth_url}")
        response = requests.post(
            oauth_url,
            data=data,
            headers=headers,
            timeout=30,
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
        
        if not access_token:
            logger.error(f"[OM][OAuth] Pas d'access_token dans la réponse: {result}")
            raise OrangeMoneyAuthError("Access token manquant dans la réponse OAuth")
        
        logger.info("[OM][OAuth] Token obtenu avec succès")
        return access_token
        
    except requests.RequestException as e:
        logger.error(f"[OM][OAuth] Erreur réseau: {e}", exc_info=True)
        raise OrangeMoneyAuthError(f"Erreur réseau lors de l'authentification: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"[OM][OAuth] Réponse non-JSON: {e}")
        raise OrangeMoneyAuthError(f"Réponse invalide de l'API OAuth: {e}")


def initiate_payment(
    *,
    amount: int,
    currency: str = "XOF",
    customer_msisdn: str,
    external_reference: str,
    description: str,
    return_url_success: str,
    return_url_failed: str,
    callback_url: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Initie une transaction de paiement Orange Money.
    
    Args:
        amount: Montant en XOF (entier)
        currency: Devise (par défaut XOF)
        customer_msisdn: Numéro téléphone client (ex: 22377011011234)
        external_reference: Référence unique de la transaction (côté AuditShield)
        description: Description du paiement
        return_url_success: URL de retour en cas de succès
        return_url_failed: URL de retour en cas d'échec
        callback_url: URL de callback/webhook (serveur-à-serveur)
        **kwargs: Paramètres additionnels (merchant_id, etc.)
    
    Returns:
        Dict contenant:
        - transaction_id: ID transaction Orange Money
        - payment_url: URL de redirection OU None si flow STK push
        - status: Statut initial (PENDING, INITIATED, etc.)
        - raw_response: Réponse complète de l'API
    
    Raises:
        OrangeMoneyAPIError: Si l'appel API échoue
        OrangeMoneyConfigurationError: Si la configuration est manquante
    """
    config = get_orange_money_config()
    
    # Obtenir l'access token
    try:
        access_token = get_access_token()
    except OrangeMoneyAuthError as e:
        logger.error(f"[OM][initiate] Erreur OAuth: {e}")
        raise
    
    # URL de collecte (100% paramétrable via settings/env)
    collect_url = config.get("COLLECT_URL")
    if not collect_url:
        # Fallback : construire depuis API_BASE_URL si COLLECT_URL non défini
        api_base_url = config.get("API_BASE_URL", "https://api.orange.com")
        # NOTE: L'URL exacte pour Mali peut varier selon la doc officielle
        # Ici on utilise un pattern générique, à adapter selon la doc OM Mali
        collect_url = f"{api_base_url.rstrip('/')}/orange-money-webpay/ml/v1/transaction/init"
        logger.warning(
            f"[OM][initiate] COLLECT_URL non défini, utilisation du fallback: {collect_url}"
        )
    
    # Construire le payload
    merchant_id = kwargs.get("merchant_id") or config.get("MERCHANT_ID", "")
    
    payload = {
        "amount": amount,
        "currency": currency,
        "customer_msisdn": customer_msisdn,
        "reference": external_reference,
        "description": description,
        "return_url_success": return_url_success,
        "return_url_failed": return_url_failed,
        "callback_url": callback_url,
    }
    
    # Ajouter merchant_id si disponible
    if merchant_id:
        payload["merchant_id"] = merchant_id
    
    # Ajouter les paramètres additionnels
    payload.update(kwargs)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    try:
        logger.info(
            f"[OM][initiate] Initiating payment: ref={external_reference}, "
            f"amount={amount} {currency}, msisdn={customer_msisdn}"
        )
        logger.debug(f"[OM][initiate] Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            collect_url,
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        # Log de la réponse (sans secrets)
        log_payload = payload.copy()
        if "merchant_key" in log_payload:
            log_payload["merchant_key"] = "***"
        logger.info(
            f"[OM][initiate] Response status={response.status_code}, "
            f"body={response.text[:500]}"
        )
        
        if response.status_code >= 400:
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {"error": response.text}
            
            logger.error(
                f"[OM][initiate] HTTP {response.status_code}: {error_data}"
            )
            raise OrangeMoneyAPIError(
                f"Erreur API Orange Money {response.status_code}",
                status_code=response.status_code,
                response_data=error_data,
            )
        
        result = response.json()
        
        # Extraire les informations pertinentes
        transaction_id = result.get("transaction_id") or result.get("id")
        payment_url = result.get("payment_url") or result.get("redirect_url")
        status = result.get("status", "PENDING")
        
        # Si pas de payment_url, c'est probablement un flow STK push
        # (demande envoyée sur le téléphone du client)
        if not payment_url:
            logger.info(
                f"[OM][initiate] Pas de payment_url, flow STK push probable "
                f"(transaction_id={transaction_id})"
            )
        
        return {
            "transaction_id": transaction_id,
            "payment_url": payment_url,
            "status": status,
            "raw_response": result,
        }
        
    except requests.RequestException as e:
        logger.error(f"[OM][initiate] Erreur réseau: {e}", exc_info=True)
        raise OrangeMoneyAPIError(f"Erreur réseau lors de l'initiation: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"[OM][initiate] Réponse non-JSON: {e}")
        raise OrangeMoneyAPIError(f"Réponse invalide de l'API: {e}")

