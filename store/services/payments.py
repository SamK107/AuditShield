# store/services/payments.py
"""
Service de finalisation des paiements pour AuditShield.
Gère la logique commune après un paiement réussi (CinetPay, Orange Money, etc.).
"""
import logging
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def finalize_successful_payment(payment) -> bool:
    """
    Finalise un paiement réussi en créant les droits de téléchargement et en envoyant l'email.
    
    Args:
        payment: Instance du modèle Order ou Payment
    
    Returns:
        bool: True si la finalisation s'est bien passée, False sinon
    """
    try:
        # Créer les tokens de téléchargement
        success = create_download_entitlements(payment)
        if not success:
            logger.error(f"[PAYMENTS] Échec création entitlements pour {payment}")
            return False
        
        # Envoyer l'email de confirmation avec les liens
        success = send_payment_confirmation_email(payment)
        if not success:
            logger.error(f"[PAYMENTS] Échec envoi email pour {payment}")
            return False
        
        logger.info(f"[PAYMENTS] Finalisation réussie pour {payment}")
        return True
        
    except Exception as e:
        logger.exception(f"[PAYMENTS] Erreur lors de la finalisation de {payment}: {e}")
        return False


def create_download_entitlements(payment) -> bool:
    """
    Crée les droits de téléchargement (tokens) pour un paiement réussi.
    
    Args:
        payment: Instance du modèle Order
    
    Returns:
        bool: True si créé avec succès, False sinon
    """
    try:
        from store.models import DownloadToken
        import secrets
        from datetime import timedelta
        
        # Vérifier si un token existe déjà
        existing_token = DownloadToken.objects.filter(order=payment).first()
        if existing_token:
            logger.info(f"[PAYMENTS] Token déjà existant pour {payment}")
            return True
        
        # Créer un nouveau token
        token_value = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(hours=72)  # 72h par défaut
        
        download_token = DownloadToken.objects.create(
            order=payment,
            token=token_value,
            expires_at=expires_at,
            max_uses=5,  # Permettre plusieurs téléchargements
            used_count=0,
        )
        
        logger.info(f"[PAYMENTS] Token créé: {download_token.token} pour {payment}")
        return True
        
    except Exception as e:
        logger.exception(f"[PAYMENTS] Erreur création token pour {payment}: {e}")
        return False


def send_payment_confirmation_email(payment) -> bool:
    """
    Envoie l'email de confirmation avec les liens de téléchargement.
    
    Args:
        payment: Instance du modèle Order
    
    Returns:
        bool: True si envoyé avec succès, False sinon
    """
    try:
        from store.models import DownloadToken
        
        # Récupérer le token de téléchargement
        download_token = DownloadToken.objects.filter(order=payment).first()
        if not download_token:
            logger.error(f"[PAYMENTS] Aucun token trouvé pour {payment}")
            return False
        
        # Construire les URLs de téléchargement
        base_url = getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000')
        download_urls = {
            'pdf_a4': f"{base_url}/downloads/secure/{payment.uuid}/?format=a4",
            'pdf_6x9': f"{base_url}/downloads/secure/{payment.uuid}/?format=6x9",
            'bonus_kit': f"{base_url}/downloads/secure/{payment.uuid}/?format=bonus",
        }
        
        # Préparer le contexte pour le template
        context = {
            'payment': payment,
            'customer_name': f"{payment.first_name} {payment.last_name}".strip(),
            'product_title': payment.product.title,
            'download_urls': download_urls,
            'download_token': download_token,
            'expires_at': download_token.expires_at,
        }
        
        # Générer le contenu de l'email
        subject = f"Votre ebook \"{payment.product.title}\" est prêt !"
        
        # Version HTML
        try:
            html_content = render_to_string('store/emails/payment_success.html', context)
        except Exception:
            html_content = None
            logger.warning("[PAYMENTS] Template HTML non trouvé, utilisation du texte seul")
        
        # Version texte
        text_content = render_to_string('store/emails/payment_success.txt', context)
        
        # Envoyer l'email
        email = EmailMessage(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'contact@auditsanspeur.com'),
            to=[payment.email],
            reply_to=[getattr(settings, 'CONTACT_INBOX_EMAIL', 'contact@auditsanspeur.com')],
        )
        
        if html_content:
            email.attach_alternative(html_content, "text/html")
        
        email.send(fail_silently=False)
        
        logger.info(f"[PAYMENTS] Email envoyé à {payment.email} pour {payment}")
        return True
        
    except Exception as e:
        logger.exception(f"[PAYMENTS] Erreur envoi email pour {payment}: {e}")
        return False


def get_payment_by_provider_reference(provider_ref: str, provider: str = None):
    """
    Récupère un paiement par sa référence provider.
    
    Args:
        provider_ref: Référence du provider (CinetPay, Orange Money, etc.)
        provider: Type de provider (optionnel)
    
    Returns:
        Instance Order ou None
    """
    try:
        from store.models import Order
        
        # Chercher par provider_ref
        order = Order.objects.filter(provider_ref=provider_ref).first()
        if order:
            return order
        
        # Fallback: chercher par cinetpay_payment_id pour compatibilité
        order = Order.objects.filter(cinetpay_payment_id=provider_ref).first()
        if order:
            return order
        
        logger.warning(f"[PAYMENTS] Aucun paiement trouvé pour provider_ref={provider_ref}")
        return None
        
    except Exception as e:
        logger.exception(f"[PAYMENTS] Erreur recherche paiement {provider_ref}: {e}")
        return None
