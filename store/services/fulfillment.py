from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from store.models import Order

logger = logging.getLogger(__name__)


def after_payment(order: "Order") -> None:
    logger.info(f"[FULFILLMENT] Start for order={order.id} provider_ref={getattr(order,'provider_ref',None)} paid_at={order.paid_at}")

    links = []
    try:
        from downloads.services import attach_links_to_order
        links = attach_links_to_order(order)
    except Exception:
        logger.exception("[FULFILLMENT] Génération des liens a échoué (non bloquant).")

    # Bonus éventuels (optionnels)
    try:
        # Laisse en place si tu ajoutes un module de bonus ensuite
        pass
    except Exception:
        logger.exception("[FULFILLMENT] Bonus: erreur (non bloquant).")

    try:
        # Email complet (liens ebook, ressources, bonus tokenisé)
        from store.services.mailing import send_fulfilment_email
        send_fulfilment_email(to_email=order.email, order_ref=getattr(order, "provider_ref", None))
    except Exception:
        logger.exception("[FULFILLMENT] Email client (mailing): échec (non bloquant).")
        # Fallback minimal (liens produits uniquement)
        try:
            from store.emails import send_payment_links
            send_payment_links(order, links=links)
        except Exception:
            logger.exception("[FULFILLMENT] Email client (fallback): échec (non bloquant).")

    logger.info(f"[FULFILLMENT] Done for order={order.id}")

