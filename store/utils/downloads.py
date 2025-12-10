# store/utils/downloads.py
from django.conf import settings
from django.urls import reverse
from store.models import Order, DownloadToken


def build_download_urls_for_order(order: Order) -> dict:
    """
    Construit les URLs de téléchargement (ebook + bonus + renvoi des liens)
    à partir d'une Order et de son DownloadToken associé.
    Utilise settings.SITE_URL comme base.
    
    Returns:
        dict: {
            'download_secure_url': str,
            'resources_url': str,
            'resend_links_url': str,
        }
    """
    base_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000").rstrip("/")
    
    # Récupérer le token lié à la commande, si présent
    token_value = None
    try:
        token_obj = order.download_token
        token_value = token_obj.token
    except DownloadToken.DoesNotExist:
        token_obj = None
    
    # URL sécurisée de téléchargement : avec token si disponible, sinon UUID seul
    if token_value:
        download_secure_url = f"{base_url}/downloads/secure/{order.uuid}/{token_value}/"
    else:
        download_secure_url = f"{base_url}/downloads/secure/{order.uuid}/"
    
    # URL ressources bonus
    resources_url = f"{base_url}/downloads/resources/{order.uuid}/"
    
    # URL pour renvoyer les liens par email
    try:
        resend_links_path = reverse("downloads:resend_links")
    except:
        # Fallback si le namespace n'existe pas
        resend_links_path = "/downloads/resend-links/"
    resend_links_url = f"{base_url}{resend_links_path}"
    
    return {
        "download_secure_url": download_secure_url,
        "resources_url": resources_url,
        "resend_links_url": resend_links_url,
    }
