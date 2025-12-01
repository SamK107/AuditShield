# store/services/kit_orders.py
"""
Service pour la gestion des commandes Kit personnalisé.
"""
import logging
from datetime import timedelta
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from store.models import KitOrder, ClientInquiry, Order

logger = logging.getLogger(__name__)


# Mapping des codes de tier vers les offres KitOrder
# Note: Les constantes KitOrder sont définies dans le modèle
TIER_TO_OFFER_MAP = {
    "essentiel_plus": "ESSENTIEL_PLUS",
    "complete_pro": "COMPLET_PRO",
    "expert_audit": "EXPERT_AUDIT",
}

# Délais estimés en heures ouvrables par offre
OFFER_DELAY_HOURS = {
    "ESSENTIEL_PLUS": 72,  # 3 jours
    "COMPLET_PRO": 96,  # 4-5 jours
    "EXPERT_AUDIT": 120,  # 5-7 jours
}


def create_kit_order_from_payment(
    order: Order,
    inquiry: Optional[ClientInquiry] = None,
) -> KitOrder:
    """
    Crée ou met à jour un KitOrder après confirmation de paiement.

    Args:
        order: L'Order Django qui vient d'être payée
        inquiry: Optionnel, la ClientInquiry associée

    Returns:
        L'instance KitOrder créée ou mise à jour
    """
    # Récupérer l'inquiry si non fourni
    if not inquiry:
        inquiry = getattr(order, "inquiries", None)
        if inquiry:
            inquiry = inquiry.filter(kind=ClientInquiry.KIND_KIT).first()
        if not inquiry:
            inquiry = ClientInquiry.objects.filter(
                order=order, kind=ClientInquiry.KIND_KIT
            ).first()

    if not inquiry:
        raise ValueError(
            f"Aucune ClientInquiry de type KIT trouvée pour Order {order.id}"
        )

    # Déterminer l'offre
    tier_code = inquiry.selected_tier_code or "complete_pro"
    offer = TIER_TO_OFFER_MAP.get(tier_code, "COMPLET_PRO")

    # Récupérer ou créer le KitOrder
    kit_order, created = KitOrder.objects.get_or_create(
        order=order,
        defaults={
            "full_name": inquiry.contact_name or order.first_name or "Client",
            "email": inquiry.email or order.email,
            "offer": offer,
            "amount": Decimal(str(order.amount_fcfa)),
            "estimated_delay_hours": OFFER_DELAY_HOURS.get(
                offer, 96
            ),
            "status": KitOrder.STATUS_PAYMENT_RECEIVED,
            "inquiry": inquiry,
            "delivery_date": _calculate_delivery_date(offer),
        },
    )

    if not created:
        # Mettre à jour si nécessaire
        kit_order.status = KitOrder.STATUS_PAYMENT_RECEIVED
        kit_order.delivery_date = _calculate_delivery_date(offer)
        kit_order.save(update_fields=["status", "delivery_date"])

    logger.info(
        f"[create_kit_order] {'Créé' if created else 'Mis à jour'} "
        f"KitOrder {kit_order.tracking_id} pour Order {order.id}"
    )

    return kit_order


def _calculate_delivery_date(offer: str) -> timezone.datetime.date:
    """
    Calcule la date de livraison estimée en fonction de l'offre.
    """
    hours = OFFER_DELAY_HOURS.get(offer, 96)
    # Convertir heures ouvrables en jours calendaires (approximatif)
    # On considère ~8h/jour ouvrable, donc 72h = 9 jours ouvrables ≈ 13 jours calendaires
    days = max(3, int(hours / 8 * 1.4))
    return (timezone.now() + timedelta(days=days)).date()


def send_kit_order_confirmation_email(kit_order: KitOrder) -> None:
    """
    Envoie l'email de confirmation après création du KitOrder.

    Args:
        kit_order: L'instance KitOrder
    """
    try:
        subject = (
            f"Votre Kit personnalisé est bien pris en charge – "
            f"Commande #{kit_order.tracking_id}"
        )

        # Rendre les templates HTML et texte
        html_message = render_to_string(
            "emails/kit_order_received.html",
            {"order": kit_order},
        )
        text_message = render_to_string(
            "emails/kit_order_received.txt",
            {"order": kit_order},
        )

        # Envoyer l'email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[kit_order.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(
            f"[send_kit_order_confirmation_email] "
            f"Email envoyé pour KitOrder {kit_order.tracking_id}"
        )
    except Exception as e:
        logger.exception(
            f"[send_kit_order_confirmation_email] "
            f"Erreur envoi email pour KitOrder {kit_order.tracking_id}: {e}"
        )
        raise

