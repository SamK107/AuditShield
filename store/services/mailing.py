from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from downloads.models import (
    DownloadableAsset,
    DownloadCategory,
    ExternalEntitlement,
)
from downloads.services import SignedUrlService
from security.links import issue_bonus_start_link


def _get_site_base_url() -> str:
    # Priorité: SITE_BASE_URL > SITE_URL > défaut local
    base = (
        getattr(settings, "SITE_BASE_URL", "")
        or getattr(settings, "SITE_URL", "")
        or "http://127.0.0.1:8000"
    )
    return base.rstrip("/")


def _ebook_variant_assets() -> list[DownloadableAsset]:
    # Prefer assets in category 'ebook'; fallback by title regex anywhere
    qs = DownloadableAsset.objects.filter(
        category__slug="ebook",
        is_published=True,
        title__iregex=r"A4|6.?x.?9",
    )
    if qs.exists():
        return list(qs.order_by("title"))
    return list(
        DownloadableAsset.objects.filter(
            is_published=True,
            title__iregex=r"A4|6.?x.?9",
        ).order_by("title")
    )


def _signed_links_for_entitlements(email: str) -> list[dict]:
    links: list[dict] = []
    # EBOOK A4/6x9
    for asset in _ebook_variant_assets():
        try:
            signed_url = SignedUrlService.get_signed_url(asset, expires=60 * 15)
            links.append({"title": asset.title, "url": signed_url})
        except Exception:
            continue
    # Other categories (if any entitlement exists)
    extra_slugs = ("checklists", "outils-pratiques", "irregularites", "bonus")
    ent_cats = (
        ExternalEntitlement.objects.filter(
            email__iexact=email,
            category__slug__in=extra_slugs,
        )
        .values_list("category__slug", flat=True)
        .distinct()
    )
    for slug in ent_cats:
        cat = DownloadCategory.objects.filter(slug=slug).first()
        if not cat:
            continue
        for asset in cat.assets.filter(is_published=True).order_by("order"):
            try:
                signed_url = SignedUrlService.get_signed_url(asset, expires=60 * 15)
                links.append({"title": f"{cat.title} — {asset.title}", "url": signed_url})
            except Exception:
                continue
    return links


def send_fulfilment_email(*, to_email: str, order_ref: str | None = None) -> None:
    """
    Envoie l'email de fulfilment (achats site ou externes) avec:
    - liens signés ebook A4/6x9
    - autres bonus/ressources en fonction des entitlements
    - lien tokenisé /bonus/kit-preparation/start
    """
    base_url = _get_site_base_url()
    links = _signed_links_for_entitlements(to_email)
    bonus_link = None
    if order_ref:
        bonus_link = issue_bonus_start_link(
            order_ref=order_ref,
            email=to_email,
            base_url=base_url,
        )

    # URL unique "toutes ressources" basée sur la commande (si retrouvable)
    resources_url: str | None = None
    if order_ref:
        try:
            from store.models import Order
            # Retrouver l'ordre via différentes clés possibles
            order = (
                Order.objects.filter(provider_ref=order_ref).first()
                or Order.objects.filter(
                    cinetpay_payment_id=order_ref
                ).first()
                or Order.objects.filter(uuid=order_ref).first()
            )
            if order:
                from django.urls import reverse
                resources_url = f"{base_url}{reverse('downloads:resources', args=[order.uuid])}"
        except Exception:
            resources_url = None

    ctx = {
        "links": links,
        "bonus_link": bonus_link,
        "resources_url": resources_url,
    }
    subject = "Vos téléchargements AuditShield"
    sender = (
        getattr(settings, "FULFILMENT_SENDER", None)
        or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    )
    text_body = render_to_string("emails/fulfilment_purchase.txt", ctx)
    html_body = render_to_string("emails/fulfilment_purchase.html", ctx)
    msg = EmailMultiAlternatives(
        subject=subject, body=text_body, from_email=sender, to=[to_email]
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


def send_bonus_published_email(*, to_email: str, pdf_url: str) -> None:
    """
    Envoie l'email quand le PDF validé est publié (Kit).
    """
    subject = "Kit de préparation — Votre PDF est prêt"
    sender = getattr(settings, "FULFILMENT_SENDER", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)
    ctx = {"pdf_url": pdf_url}
    text_body = render_to_string("emails/bonus_published.txt", ctx)
    html_body = render_to_string("emails/bonus_published.html", ctx)
    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=sender, to=[to_email])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)


