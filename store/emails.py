from __future__ import annotations
import os
from typing import Iterable, Dict, Any
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000")


def _abs(url_path: str) -> str:
    if url_path.startswith(("http://", "https://")):
        return url_path
    return f"{SITE_BASE_URL.rstrip('/')}/{url_path.lstrip('/')}"


def send_payment_links(order, links: Iterable[Dict[str, Any]] | None = None, request=None) -> None:
    if links is None:
        try:
            from downloads.services import links as dl_links
            links = dl_links.attach_links_to_order(order)
        except Exception:
            links = []

    normalized_links = []
    for l in links or []:
        l = dict(l)
        if l.get("download_url"):
            l["download_url"] = _abs(l["download_url"])
        if l.get("view_url"):
            l["view_url"] = _abs(l["view_url"])
        normalized_links.append(l)

    subject = f"[AuditSansPeur] Confirmation de paiement – {order.product.title}"
    to = [order.email]
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@auditsanspeur.com")

    context = {
        "order": order,
        "links": normalized_links,
        "site_base_url": SITE_BASE_URL,
        "is_kit": getattr(order, "offer_code", "STANDARD").upper() in {"KIT_COMPLET", "KIT", "KIT_PLUS"},
    }

    text_body = render_to_string("emails/paid_links.txt", context)
    html_body = render_to_string("emails/paid_links.html", context)

    msg = EmailMultiAlternatives(subject, text_body, from_email, to)
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)

