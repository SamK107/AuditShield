# store/views.py
import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)
logger.warning("STORE.VIEWS LOADED FROM %s", __file__)
import os
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, send_mail
from django.db.models import Prefetch
from django.http import FileResponse, Http404, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

import store.services.cinetpay as cinetpay
from store.services.cinetpay import verify_signature, payment_check
from downloads.models import DownloadableAsset
from store.content.faqs import FAQ_ITEMS
from downloads.services import user_has_access

from pathlib import Path
from django.shortcuts import render, get_object_or_404
from downloads.models import DownloadableAsset, DownloadCategory

from .forms import CheckoutForm, KitInquiryForm, TrainingInquiryForm
from django.conf import settings
common_note = getattr(settings, "EXTERNAL_BUY_LINKS_NOTE", "")

# Slugs attendus par l’ebook (aligne-les aux slugs réels de l’admin si besoin)
SLUG_CHECKLISTS = "checklists"
SLUG_BONUS = "bonus"
SLUG_OUTILS = "outils-pratiques"
SLUG_IRREGS = "irregularites"

def _render_assets_by_category(request, cat_slug, template_name="store/downloads_list.html"):
    category = DownloadCategory.objects.filter(slug=cat_slug).first()
    if not category:
        from django.http import Http404
        raise Http404("Catégorie introuvable")

    # Si la catégorie est protégée, vérifier l'accès
    if getattr(category, "is_protected", False) and not user_has_access(request, category):
        from django.shortcuts import redirect
        return redirect(f"/claim/?slug={category.slug}&next=/{cat_slug}")

    assets = DownloadableAsset.objects.filter(category=category).order_by("id") if category else []
    ctx = {"category": category, "assets": assets, "cat_slug": cat_slug}
    return render(request, template_name, ctx)

def downloads_checklists(request):
    return _render_assets_by_category(request, SLUG_CHECKLISTS)

def downloads_bonus(request):
    return _render_assets_by_category(request, SLUG_BONUS)

def downloads_outils(request):
    return _render_assets_by_category(request, SLUG_OUTILS)

def downloads_irregularites(request):
    return _render_assets_by_category(request, SLUG_IRREGS)
  # ta logique d'entitlement

from .models import (
    DownloadToken,
    ExampleSlide,
    InquiryDocument,
    IrregularityCategory,
    IrregularityRow,
    MediaAsset,
    OfferTier,
    Order,
    Payment,
    PaymentEvent,
    PaymentWebhookLog,
    PreliminaryTable,
    Product,
)
from .seeds.ebook_irregularities import SEED_IRREGULARITIES


def get_webhook_header():
    """Return the configured HTTP header key for legacy/form CinetPay webhooks."""
    return os.getenv("CINETPAY_WEBHOOK_HEADER", "x-token")


# ---- Pages ----

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_published=True)
    media = MediaAsset.objects.filter(product=product)
    proofs = product.social_proofs_json or []
    standard_tier = OfferTier.objects.filter(product=product, kind="STANDARD").first()

    rows_ebook = SEED_IRREGULARITIES.get(slug, [])

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "media": media,
            "faqs": FAQ_ITEMS,
            "proofs": proofs,
            "standard_tier": standard_tier,
            "rows_ebook": rows_ebook,
        },
    )


def offers(request):
    product = Product.objects.filter(is_published=True).first()
    tiers_qs = OfferTier.objects.filter(product=product) if product else OfferTier.objects.none()

    standard = kit = formation = None
    for t in tiers_qs:
        label = (getattr(t, "get_kind_display", lambda: "")() or t.title or "").lower()
        combo = " ".join([getattr(t, "slug", "") or "", t.title or "", label])
        if "ebook" in combo or "standard" in combo:
            standard = t
        elif "personnalis" in combo or "kit" in combo or "adapt" in combo:
            kit = t
        elif "formation" in combo or "assistance" in combo:
            formation = t
    if standard is None and tiers_qs.exists():
        standard = tiers_qs.order_by("order", "id").first()
    if kit is None and tiers_qs.count() >= 2:
        kit = tiers_qs.order_by("order", "id")[1]
    if formation is None and tiers_qs.count() >= 3:
        formation = tiers_qs.order_by("order", "id")[2]

    return render(
        request,
        "store/offers.html",
        {"product": product, "standard": standard, "kit": kit, "formation": formation},
    )

def debug_host_view(request):
    return HttpResponse(f"Host reçu par Django : {request.get_host()}")
    
@require_http_methods(["GET", "POST"])
def kit_inquiry(request):
    MAX_ATTACH_TOTAL = 15 * 1024 * 1024  # 15 Mo
    MAX_FILES = 10
    MAX_FILE_SIZE = 10 * 1024 * 1024
    ALLOWED_EXTS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".gif"]
    INQUIRY_TO = ["contact@auditsanspeur.com"]

    def _total_size(files):
        return sum(getattr(f, "size", 0) for f in files)

    if request.method == "POST":
        form = KitInquiryForm(request.POST)
        files = request.FILES.getlist("documents")
        file_errors = []
        if files:
            if len(files) > MAX_FILES:
                file_errors.append(f"Limité à {MAX_FILES} fichiers.")
            import os
            for f in files:
                ext = os.path.splitext(f.name)[1].lower()
                if ext not in ALLOWED_EXTS:
                    file_errors.append(f"Type non autorisé : {ext}")
                if f.size > MAX_FILE_SIZE:
                    file_errors.append(f"{f.name} dépasse 10 Mo.")
        if file_errors:
            for err in file_errors:
                form.add_error("documents", err)
        if form.is_valid() and not file_errors:
            inquiry = form.save()
            for f in files:
                InquiryDocument.objects.create(inquiry=inquiry, file=f, original_name=f.name)
            data = form.cleaned_data
            subject = "Demande – Kit personnalisé"
            lines = [
                "Nouvelle demande de Kit personnalisé :",
                f"- Nom          : {data['contact_name']}",
                f"- Email        : {data['email']}",
                f"- Organisation : {data['organization_name']}",
                f"- Téléphone    : {data.get('phone') or '—'}",
                f"- Statut       : {data.get('statut_juridique') or '—'}",
                f"- Localisation : {data.get('location') or '—'}",
                f"- Secteur      : {data.get('sector') or '—'}",
                f"- Budget       : {data.get('budget_range') or '—'}",
                f"- Missions     : {data.get('mission_text') or '—'}",
                "",
                "DÉTAILS (optionnels) :",
                f"- Financement  : {', '.join(data.get('funding_sources', [])) or '—'}",
                f"- Audits       : {', '.join(data.get('audits_types', [])) or '—'}",
                f"- Fréquence    : {data.get('audits_frequency') or '—'}",
                f"- Taille       : {data.get('staff_size') or '—'}",
                f"- Organigramme : {data.get('org_chart_text') or '—'}",
                f"- Notes        : {data.get('notes_text') or '—'}",
            ]
            body = "\n".join(lines)
            try:
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    to=INQUIRY_TO,
                    reply_to=[data["email"]],
                )
                if _total_size(files) <= MAX_ATTACH_TOTAL:
                    for f in files:
                        email.attach(
                            f.name,
                            f.read(),
                            f.content_type or "application/octet-stream",
                        )
                else:
                    if files:
                        names = "\n".join(f"- {f.name}" for f in files)
                        email.body += "\n\nFichiers reçus (non attachés car volumineux) :\n" + names
                email.send(fail_silently=True)
                messages.success(
                    request,
                    "Merci, votre demande a bien été envoyée. "
                    "Nous vous contactons sous 24–48 h avec une proposition adaptée.",
                )
            except Exception:
                logging.getLogger(__name__).exception("Erreur d'envoi email (kit)")
                messages.info(
                    request,
                    "Votre demande est enregistrée. "
                    "Un souci d'email est survenu ; nous vous recontactons vite.",
                )
            return redirect(reverse("store:kit_inquiry_success"))
    else:
        form = KitInquiryForm()
    return render(request, "store/forms/kit_inquiry.html", {"form": form})


def kit_inquiry_success(request):
    return render(request, "store/forms/kit_inquiry_success.html")


MAX_ATTACH_TOTAL = 15 * 1024 * 1024  # 15 Mo
MAX_FILES = 10
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".gif"]


def total_size(files):
    return sum(getattr(f, "size", 0) for f in files)


INQUIRY_TO = ["contact@auditsanspeur.com"]
MAX_ATTACH_TOTAL = 15 * 1024 * 1024


def _total_size(files):
    return sum(getattr(f, "size", 0) for f in files)


def training_inquiry_view(request):
    if request.method == "POST":
        form = TrainingInquiryForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            files = request.FILES.getlist("documents")
            program = data.get("program_title") or "Programme de formation (Audit Sans Peur)"

            subject = f"Demande – Formation & Assistance — {program}"
            lines = [
                "Nouvelle demande de formation :",
                f"- Programme    : {program}",
                f"- Nom          : {data['contact_name']}",
                f"- Email        : {data['email']}",
                f"- Organisation : {data['organization_name']}",
                "",
                "Contexte & objectifs :",
                f"{data['message']}",
                "",
                "DÉTAILS (optionnels) :",
                f"- Téléphone    : {data.get('phone') or '—'}",
                f"- Participants : {data.get('participants_count') or '—'}",
                f"- Format       : {dict(form.fields['delivery_mode'].choices).get(data.get('delivery_mode'), '—')}",
                f"- Période      : {data.get('preferred_dates') or '—'}",
            ]
            body = "\n".join(lines)

            try:
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=["contact@auditsanspeur.com"],
                    reply_to=[data["email"]],
                )
                email.send(fail_silently=False)
                messages.success(
                    request,
                    "Merci, votre demande a bien été envoyée. Nous vous contactons sous 24–48 h.",
                )
            except Exception:
                logging.getLogger(__name__).exception("Erreur d'envoi email")
                messages.info(
                    request,
                    "Votre demande est enregistrée. Un souci d'email est survenu ; nous vous recontactons vite.",
                )

            if _total_size(files) <= MAX_ATTACH_TOTAL:
                for f in files:
                    email.attach(f.name, f.read(), f.content_type or "application/octet-stream")
            else:
                if files:
                    names = "\n".join(f"- {f.name}" for f in files)
                    email.body += "\n\nFichiers reçus (non attachés car volumineux) :\n" + names

            email.send(fail_silently=False)

            messages.success(
                request,
                "Merci, votre demande a bien été envoyée. Nous vous contactons sous 24–48 h avec une proposition adaptée.",
            )
            return redirect(reverse("store:training_inquiry_success"))
    else:
        form = TrainingInquiryForm()

    return render(request, "store/training_inquiry.html", {"form": form})


def training_inquiry_success(request):
    return render(request, "store/training_inquiry_success.html")


def examples(request):
    product = Product.objects.filter(is_published=True).first()
    slides = ExampleSlide.objects.filter(product=product) if product else []
    return render(request, "store/examples.html", {"product": product, "slides": slides})


@require_http_methods(["GET"])
def irregularities_table(request):
    version = request.GET.get("version", "EBOOK")
    product = Product.objects.filter(is_published=True).first()
    rows = (
        IrregularityRow.objects.filter(product=product, version=version).order_by("order")[:5]
        if product
        else []
    )
    return render(
        request, "store/partials/irregularities_table.html", {"rows": rows, "version": version}
    )


# ---- Paiement ----

@require_http_methods(["GET", "POST"])
def buy(request, slug):
    product = get_object_or_404(Product, slug=slug, is_published=True)
    standard_tier = OfferTier.objects.filter(product=product, kind="STANDARD").first()
    tier = None
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            tier_id = standard_tier.id if standard_tier else None
            if not tier_id:
                return render(
                    request,
                    "store/payment_error.html",
                    {"message": "Offre invalide."},
                    status=400,
                )
            tier = get_object_or_404(OfferTier, id=tier_id, product=product)
            transaction_id = uuid.uuid4().hex[:24].upper()
            amount = tier.price_fcfa or product.price_fcfa
            order = Order.objects.create(
                product=product,
                tier_id=tier.id if tier else None,
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
                phone=form.cleaned_data.get("phone", ""),
                amount_fcfa=amount,
                currency="XOF",
                status="CREATED",
                provider_ref=f"ORDER-{uuid.uuid4().hex}",
            )
            try:
                payment_url = cinetpay.init_payment_auto(order=order, request=request)
            except Exception:
                order.delete()
                return render(
                    request,
                    "store/payment_error.html",
                    {"message": "Erreur lors de l'initialisation du paiement."},
                    status=500,
                )
            return redirect(payment_url)
    else:
        form = CheckoutForm()
    return render(
        request,
        "store/checkout.html",
        {"form": form, "product": product, "tier": tier or standard_tier},
    )


def payment_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    product = order.product
    download_url = None
    if product.download_slug:
        asset = DownloadableAsset.objects.filter(slug=product.download_slug).first()
        if asset:
            download_url = asset.get_absolute_url() if hasattr(asset, "get_absolute_url") else None
    return render(
        request, "store/payment_success.html", {"order": order, "download_url": download_url}
    )


# --- Paiement CinetPay sécurisé ---
import json

from django.db import transaction
from django.views.decorators.http import require_POST

try:
    from store.models import PaymentEvent  # optional
except Exception:
    PaymentEvent = None

from django.utils import timezone  # éventuellement utile


def _sigdebug(header_name, sig, raw):
    """Log non-sensitive signature diag when CINETPAY_SIG_DEBUG=1."""
    if os.getenv("CINETPAY_SIG_DEBUG") != "1":
        return
    secret = os.getenv("CINETPAY_WEBHOOK_SECRET") or ""
    logging.getLogger(__name__).warning(
        "[SIGDEBUG] header=%s provided[:24]=%s body_len=%d body_sha256=%s secret_sha256[:24]=%s",
        header_name,
        str(sig)[:24],
        len(raw or b""),
        hashlib.sha256(raw or b"").hexdigest(),
        hashlib.sha256(secret.encode()).hexdigest()[:24],
    )


@require_POST
def start_checkout(request, product_slug, tier_id):
    import uuid
    from .models import OfferTier, Product

    product = get_object_or_404(Product, slug=product_slug, is_published=True)
    tier = get_object_or_404(OfferTier, id=tier_id, product=product)
    email = request.POST.get("email")
    if not email:
        return JsonResponse({"error": "Email requis"}, status=400)
    amount = tier.price_fcfa or product.price_fcfa
    order_id = uuid.uuid4().hex[:32]
    payment = Payment.objects.create(
        order_id=order_id,
        amount=amount,
        currency="XOF",
        email=email,
        status="INIT",
    )
    if PaymentEvent:
        PaymentEvent.objects.create(
            payment=payment, kind="INIT", payload={"amount": amount, "email": email}
        )
    try:
        pay_url = cinetpay.init_payment_auto(order=payment, request=request)
    except Exception as e:
        payment.status = "FAILED"
        payment.save(update_fields=["status"])
        if PaymentEvent:
            PaymentEvent.objects.create(payment=payment, kind="ERROR", payload={"error": str(e)})
        return JsonResponse({"error": "Erreur lors de l'initialisation du paiement."}, status=500)
    payment.status = "PENDING"
    payment.save(update_fields=["status"])
    if PaymentEvent:
        PaymentEvent.objects.create(payment=payment, kind="PENDING", payload={"pay_url": pay_url})
    return JsonResponse({"redirect_url": pay_url})


def payment_return(request):
    transaction_id = request.GET.get("transaction_id")
    if not transaction_id:
        return render(request, "store/payment_return.html")
    order = get_object_or_404(Order, transaction_id=transaction_id)
    request.session["order_email"] = order.email
    paid = set(request.session.get("paid_orders", []))
    paid.add(str(order.uuid))
    request.session["paid_orders"] = list(paid)
    return redirect("downloads:secure", order_uuid=order.uuid)


@csrf_exempt
@require_POST
def cinetpay_callback(request):
    """
    Legacy/alt webhook with custom header (x-token) + verify_signature + S2S check.
    """
    import hashlib as _hl

    header_name = get_webhook_header()
    sig = request.headers.get(header_name) or request.META.get(
        f"HTTP_{header_name.upper().replace('-','_')}"
    )
    raw = request.body or b""
    _sigdebug(header_name, sig, raw)
    if not sig or not verify_signature(sig, raw):
        logging.getLogger(__name__).warning(
            "Invalid signature: header=%s body_len=%d body_sha256=%s",
            header_name,
            len(raw),
            _hl.sha256(raw).hexdigest(),
        )
        return HttpResponseBadRequest("Invalid signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    order_id = (
        payload.get("transaction_id") or payload.get("cpm_trans_id") or payload.get("order_id")
    )
    if not order_id:
        return HttpResponseBadRequest("Missing order_id")

    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(order_id=order_id)
        except Payment.DoesNotExist:
            logging.getLogger(__name__).error("Webhook (legacy) for unknown order_id=%s", order_id)
            return JsonResponse({"ok": False, "reason": "unknown_order"}, status=200)

        if PaymentEvent:
            try:
                PaymentEvent.objects.create(payment=payment, kind="WEBHOOK", payload=payload)
            except Exception:
                logging.getLogger(__name__).exception("Failed to persist PaymentEvent for %s", order_id)

        if getattr(payment, "status", None) == "PAID":
            return JsonResponse({"ok": True, "idempotent": True}, status=200)

        try:
            amt = payload.get("amount")
            cur = payload.get("currency")
            if amt is not None and int(amt) != int(payment.amount):
                logging.getLogger(__name__).warning(
                    "Amount mismatch for %s: payload=%s db=%s", order_id, amt, payment.amount
                )
            if cur and cur != getattr(payment, "currency", None):
                logging.getLogger(__name__).warning(
                    "Currency mismatch for %s: payload=%s db=%s",
                    order_id,
                    cur,
                    getattr(payment, "currency", None),
                )
        except Exception:
            pass

        ok, provider_tx_id = payment_check(order_id)
        if not ok:
            try:
                payment.status = "FAILED"
                payment.save(update_fields=["status", "updated_at"])
            except Exception:
                payment.status = "FAILED"
                payment.save()
            if PaymentEvent:
                try:
                    PaymentEvent.objects.create(payment=payment, kind="CHECK_FAIL", payload={})
                except Exception:
                    logging.getLogger(__name__).exception("Failed to persist CHECK_FAIL for %s", order_id)
            return JsonResponse({"ok": False, "reason": "check_failed"}, status=200)

        payment.status = "PAID"
        if provider_tx_id:
            setattr(payment, "provider_tx_id", provider_tx_id)
        try:
            payment.save(update_fields=["status", "provider_tx_id", "updated_at"])
        except Exception:
            payment.save()

        if PaymentEvent:
            try:
                PaymentEvent.objects.create(
                    payment=payment, kind="CHECK_OK", payload={"provider_tx_id": provider_tx_id}
                )
            except Exception:
                logging.getLogger(__name__).exception("Failed to persist CHECK_OK for %s", order_id)

        try:
            deliver_ebook(payment)
        except Exception as e:
            logging.getLogger(__name__).exception("Delivery error for %s: %s", order_id, e)
            return JsonResponse({"ok": True, "delivered": False}, status=200)

    return JsonResponse({"ok": True, "delivered": True}, status=200)


def deliver_ebook(payment):
    """
    Génère un lien de téléchargement unique et expirable, envoie l'e-mail, journalise l'event.
    """
    from django.urls import reverse

    order = Order.objects.filter(provider_ref=payment.order_id).first()
    if not order:
        return
    token_obj, _ = DownloadToken.objects.get_or_create(order=order)
    base_url = settings.CINETPAY_RETURN_URL.rstrip("/")
    download_url = f"{base_url}" + reverse("downloads:secure_token", args=[str(token_obj.token)])
    subject = "Votre lien de téléchargement AuditShield"
    message = (
        f"Merci pour votre achat !\n\n"
        f"Téléchargez votre ebook ici (valable 72h) : {download_url}\n\n"
        f"Ceci est un lien personnel et temporaire."
    )
    send_mail(subject, message, None, [payment.email])
    if PaymentEvent:
        PaymentEvent.objects.create(
            payment=payment, kind="DELIVERED", payload={"download_url": download_url}
        )


@csrf_exempt
@require_POST
def payment_notify(request):
    """
    Ancien endpoint (compat). Conserve si déjà déclaré côté CinetPay.
    """
    try:
        try:
            payload = json.loads(request.body.decode())
        except Exception:
            logging.getLogger(__name__).warning("[CinetPay][notify] Invalid JSON")
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
        masked = {k: ("***" if "key" in k else v) for k, v in payload.items()}
        logging.getLogger(__name__).info(f"[CinetPay][notify] Payload: {masked}")
        transaction_id = payload.get("transaction_id")
        if not transaction_id:
            return JsonResponse({"detail": "Missing transaction_id"}, status=400)
        order = Order.objects.filter(provider_ref=transaction_id).first()
        if not order:
            logging.getLogger(__name__).warning("[CinetPay][notify] Order not found for transaction_id=%s", transaction_id)
            return JsonResponse({"detail": "Order not found"}, status=404)
        try:
            check = cinetpay.safe_check(transaction_id)
        except Exception as e:
            logging.getLogger(__name__).error(f"[CinetPay][notify] CinetPay check error: {str(e)}")
            return JsonResponse({"detail": "CinetPay check error"}, status=502)
        status = (check.get("data") or {}).get("status", "")
        logging.getLogger(__name__).info(f"[CinetPay][notify] Order {order.id} - check status: {status}")
        if status in ("ACCEPTED", "SUCCESS", "PAID"):
            order.status = Order.PAID
            order.save(update_fields=["status"])
            from store.services import deliver_order
            deliver_order(order)
            send_download_email(order)
        elif status in ("REFUSED", "CANCELED", "FAILED"):
            order.status = Order.FAILED
            order.save(update_fields=["status"])
        return JsonResponse({"detail": "OK"})
    except Exception as e:
        logging.getLogger(__name__).error(f"[CinetPay][notify] Unexpected error: {str(e)}")
        return JsonResponse({"detail": "Unexpected error"}, status=500)


# Webhook HMAC (form-data) — compat
SECRET = os.getenv("CINETPAY_SECRET", "")

FIELDS_ORDER = [
    "cpm_site_id",
    "cpm_trans_id",
    "cpm_trans_date",
    "cpm_amount",
    "cpm_currency",
    "signature",
    "payment_method",
    "cel_phone_num",
    "cpm_phone_prefixe",
    "cpm_language",
    "cpm_version",
    "cpm_payment_config",
    "cpm_page_action",
    "cpm_custom",
    "cpm_designation",
    "cpm_error_message",
]


def _cinetpay_token(form: dict) -> str:
    data = "".join(form.get(k, "") for k in FIELDS_ORDER)
    return hmac.new(SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()


@csrf_exempt
@require_http_methods(["POST"])
def payment_callback(request):
    received = request.headers.get("x-token", "")
    form = {k: request.POST.get(k, "") for k in FIELDS_ORDER}
    expected = _cinetpay_token(form)

    if not received or not hmac.compare_digest(received, expected):
        return HttpResponse("Invalid signature", status=400)

    tx_id = request.POST.get("cpm_trans_id")
    order = Order.objects.filter(cinetpay_payment_id=tx_id).first()
    if not order:
        return HttpResponse("Order not found", status=404)

    res = cinetpay.safe_check(tx_id)
    status_ok = res.get("code") == "00" and res.get("data", {}).get("status") == "ACCEPTED"

    if status_ok:
        order.status = Order.PAID
        order.save(update_fields=["status"])
        DownloadToken.objects.get_or_create(order=order)
    else:
        order.status = Order.FAILED
        order.save(update_fields=["status"])

    return HttpResponse("OK")


def download(request, token):
    dt = DownloadToken.objects.filter(token=token).select_related("order", "order__product").first()
    if not dt or not dt.is_valid():
        raise Http404("Lien de téléchargement invalide ou expiré.")
    product = dt.order.product
    f = product.deliverable_file
    if not f:
        raise Http404("Fichier non disponible.")
    return FileResponse(f.open("rb"), as_attachment=True, filename=f.name.split("/")[-1])


def examples_block(request):
    """
    Fragment HTMX pour la zone centrale des exemples.
    """
    mode = request.GET.get("mode", "carousel")
    version = request.GET.get("version", "EBOOK")
    product = Product.objects.filter(is_published=True).first()

    if mode == "table":
        prefetch_rows = Prefetch(
            "rows",
            queryset=IrregularityRow.objects.filter(version=version).order_by("order", "id")[:5],
            to_attr="rows_for_version",
        )
        categories = (
            IrregularityCategory.objects.filter(product=product)
            .order_by("order", "title")
            .prefetch_related(prefetch_rows)
        )
        return render(
            request,
            "store/partials/examples_block_table_carousel.html",
            {"product": product, "version": version, "categories": categories},
        )

    if mode == "prelim":
        tables = (
            PreliminaryTable.objects.filter(product=product)
            .order_by("order", "title")
            .prefetch_related("rows")
        )
        return render(
            request,
            "store/partials/examples_block_prelim_carousel.html",
            {"tables": tables},
        )

    slides = ExampleSlide.objects.filter(product=product).order_by("order", "id") if product else []
    return render(request, "store/partials/examples_block_carousel.html", {"slides": slides})


@require_http_methods(["GET"])
def examples_prelim(request):
    product = Product.objects.filter(is_published=True).first()
    tables = (
        PreliminaryTable.objects.filter(product=product)
        .order_by("order", "title")
        .prefetch_related("rows")
    )
    return render(request, "store/examples_prelim.html", {"product": product, "tables": tables})


@login_required
def user_orders(request):
    orders = Order.objects.filter(email=request.user.email).order_by("-created_at")
    return render(request, "store/user_orders.html", {"orders": orders})


def send_download_email(order):
    product = order.product
    asset = None
    download_url = None
    if product.download_slug:
        asset = DownloadableAsset.objects.filter(slug=product.download_slug).first()
        if asset:
            download_url = asset.get_absolute_url() if hasattr(asset, "get_absolute_url") else None
    if download_url:
        subject = f"Votre ebook : {product.title}"
        message = (
            f"Bonjour {order.first_name},\n\nMerci pour votre achat !\n\n"
            f"Vous pouvez télécharger votre ebook ici : {download_url}\n\n"
            f"Ce lien est personnel et réservé à votre usage.\n\nBonne lecture !\nL'équipe AuditShield"
        )
        send_mail(subject, message, None, [order.email])
    else:
        subject = "Votre achat sur AuditShield"
        message = (
            f"Bonjour {order.first_name},\n\nMerci pour votre achat ! Nous vous "
            f"enverrons votre lien de téléchargement dès que possible.\n\nL'équipe AuditShield"
        )
        send_mail(subject, message, None, [order.email])


# ---- Nouvelles vues CinetPay sécurisées ----

def _cinetpay_secret_bytes():

    """

    Secret prioritaire = SECRET_KEY dédié CinetPay ; fallback = API_KEY.

    """

    secret = settings.CINETPAY_SECRET_KEY or settings.CINETPAY_API_KEY or ""

    return secret.encode("utf-8")


def cinetpay_return(request):
    # CinetPay renvoie classiquement ?transaction_id=... ou ?cpm_trans_id=...
    tx_id = request.GET.get("cpm_trans_id") or request.GET.get("transaction_id")

    # Si on ping la route sans param (curl, monitoring, etc.) -> 200, pas d'erreur
    if not tx_id:
        return HttpResponse("OK", status=200)

    # On accepte provider_ref OU cinetpay_payment_id
    order = Order.objects.filter(
        Q(cinetpay_payment_id=tx_id) | Q(provider_ref=tx_id)
    ).first()
    if not order:
        return HttpResponse("Transaction inconnue", status=404)

    # Crée le token de téléchargement et redirige vers le choix des versions
    dt, _ = DownloadToken.objects.get_or_create(order=order)
    return redirect("store:download_options", token=dt.token)


def cinetpay_cancel(request):
    return HttpResponse("Paiement annulé.")


@csrf_exempt
def cinetpay_notify(request):
    # Version simplifiée temporaire
    if request.method == 'GET':
        return HttpResponse('OK', status=200)
    return HttpResponse('OK', status=200)

@require_http_methods(["GET"])
def download_options(request, token):
    from django.shortcuts import get_object_or_404
    from store.models import DownloadToken, Order
    dt = get_object_or_404(DownloadToken, token=token)
    if not dt.is_valid() or dt.order.status != Order.PAID:
        raise Http404("Lien de téléchargement invalide ou paiement non validé.")
    product = dt.order.product
    return render(request, "store/download_options.html", {"product": product, "token": token})


@require_http_methods(["GET"])
def download_version(request, token, version):
    from django.shortcuts import get_object_or_404
    from django.http import FileResponse, Http404
    from store.models import DownloadToken, Order
    dt = get_object_or_404(DownloadToken, token=token)
    if not dt.is_valid() or dt.order.status != Order.PAID:
        raise Http404("Lien de téléchargement invalide ou paiement non validé.")
    product = dt.order.product
    if version == 'a4':
        f = product.deliverable_file_a4
    elif version == '6x9':
        f = product.deliverable_file_6x9
    else:
        raise Http404("Version inconnue.")
    if not f:
        raise Http404("Fichier non disponible.")
    return FileResponse(f.open('rb'), as_attachment=True, filename=f.name.split('/')[-1])
    
def secure_download(request, asset_id):
    asset = get_object_or_404(DownloadableAsset, pk=asset_id)
    # Ex: vérifier droit d'accès (achat valide, email autorisé, etc.)
    if not user_has_access(request, asset.category):
        from django.shortcuts import redirect
        return redirect(f"/claim/?slug={asset.category.slug}&next=/downloads/secure/{asset_id}/")

    # Construire le chemin privé : remplace 'media' par 'private_media'
    rel_path = Path(asset.file.name)  # e.g. downloads/2025/10/fichier.pdf
    abs_path = Path(settings.PRIVATE_MEDIA_ROOT) / rel_path
    if not abs_path.exists():
        raise Http404("Not found")

    return FileResponse(open(abs_path, "rb"), as_attachment=True, filename=rel_path.name)
    
def buy_other_methods(request, product_key):
    """
    /buy/other-methods/<product_key>/ — Affiche les plateformes externes.
    Tolérant: retombe sur "produit" si la clé est inconnue.
    """
    from django.conf import settings
    links = getattr(settings, "EXTERNAL_BUY_LINKS", {}) or {}
    platforms = links.get(product_key) or links.get("produit") or {}
    note = getattr(settings, "EXTERNAL_BUY_LINKS_NOTE", "")

    if isinstance(platforms, dict):
        platforms_ctx = platforms
    elif isinstance(platforms, (list, tuple)):
        platforms_ctx = list(platforms)
    else:
        platforms_ctx = {}

    return render(
        request,
        "store/buy_other_methods.html",
        {"platforms": platforms_ctx, "note": note},
    )

def _make_bonus_token(order_ref: str, email: str) -> str:
    signer = TimestampSigner(salt="bonus-kit-preparation")
    return signer.sign(f"{order_ref}:{email}")

def _check_bonus_token(token: str) -> tuple[bool, str, str]:
    signer = TimestampSigner(salt="bonus-kit-preparation")
    try:
        value = signer.unsign(token, max_age=BONUS_TOKEN_AGE)
        order_ref, email = value.split(":", 1)
        return True, order_ref, email
    except SignatureExpired:
        return False, "", ""
    except BadSignature:
        return False, "", ""

@require_http_methods(["GET"])
def bonus_kit_landing(request):
    """
    Page /bonus/kit-preparation/ :
    - Affiche un petit formulaire "Référence de commande + Email"
    - Le bouton "Démarrer mon bonus" peut aussi accepter ?order_ref=&email= pour générer le token et rediriger.
    - Mode démo : ?demo=1 -> saute la vérif et affiche directement la page de soumission.
    """
    if request.GET.get("demo") == "1":
        ctx = {"product_slug": request.GET.get("product_slug","audit-sans-peur"), "order_ref": "DEMO-ORDER-123"}
        return TemplateResponse(request, "store/bonus_landing.html", ctx)

    order_ref = (request.GET.get("order_ref") or "").strip()
    email = (request.GET.get("email") or "").strip()

    if order_ref and email:
        token = _make_bonus_token(order_ref, email)
        return redirect(f"/bonus/kit-preparation/start?product_slug=audit-sans-peur&token={token}")

    return TemplateResponse(request, "store/bonus_landing.html", {})

@require_http_methods(["POST"])
def bonus_kit_claim(request):
    """
    Réception du petit formulaire (order_ref + email) -> génère un token et redirige vers /start
    """
    order_ref = (request.POST.get("order_ref") or "").strip()
    email = (request.POST.get("email") or "").strip()
    if not order_ref or not email:
        return TemplateResponse(request, "store/bonus_landing.html", {
            "error": "Merci d’indiquer une référence de commande et un email.",
        }, status=400)

    token = _make_bonus_token(order_ref, email)
    return redirect(f"/bonus/kit-preparation/start?product_slug=audit-sans-peur&token={token}")

@require_http_methods(["GET", "POST"])
def bonus_kit_start(request):
    """
    Page de soumission (les 3 pages à analyser).
    - Accès si token signé valide OU mode demo=1.
    """
    if request.GET.get("demo") == "1":
        ctx = {"demo": True, "product_slug": request.GET.get("product_slug","audit-sans-peur"), "order_ref": "DEMO-ORDER-123"}
        return TemplateResponse(request, "store/bonus_prelim_submit.html", ctx)

    token = request.GET.get("token") or ""
    ok, order_ref, email = _check_bonus_token(token)
    if not ok:
        # retourne au landing avec un message
        return TemplateResponse(request, "store/bonus_landing.html", {
            "error": "Accès expiré ou invalide. Merci de saisir à nouveau votre référence et email.",
        }, status=403)

    if request.method == "POST":
        # Ici tu traites la soumission (texte 3 pages, fichier, etc.)
        submitted_text = request.POST.get("text") or ""
        # TODO: persister / envoyer email / lancer pipeline…
        return TemplateResponse(request, "store/bonus_prelim_submit.html", {
            "ok": True, "message": "Votre document a bien été reçu. Merci !",
            "order_ref": order_ref, "email": email
        })

    return TemplateResponse(request, "store/bonus_prelim_submit.html", {
        "order_ref": order_ref, "email": email
    })

# -----------------------------
# BONUS: Kit de préparation
# -----------------------------
import re
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseBadRequest
from django.core.mail import send_mail, EmailMessage
from django.conf import settings

ORDER_REF_RE = re.compile(r"^SC[A-Z0-9]{5,}$", re.I)  # ex: SCD8LJ

def validate_internal_order_ref(order_ref: str, email: str) -> bool:
    """
    TODO: remplace par une vraie vérif en BD (ex: Order.objects.filter(...).exists()).
    Ici: on 'mock' : accepte une ref au format SCxxxxx et email non-vide.
    """
    if not email or not ORDER_REF_RE.match(order_ref or ""):
        return False
    return True

def validate_external_email(email: str) -> bool:
    """
    TODO: remplace par une vraie vérif contre la liste des emails transmis par les partenaires.
    Ici: on 'mock' : on accepte tout email qui contient un '@'.
    """
    return bool(email and "@" in email)

def bonus_kit_landing(request):
    # Ta template existante (bouton Démarrer => vers start)
    return render(request, "store/bonus_landing.html")

def bonus_kit_start(request):
    """
    GET  => Affiche le formulaire de soumission (texte / fichiers, email, ref / externe).
    POST => Valide & traite, puis redirige vers 'merci'.
    """
    if request.method == "GET":
        # mode DEMO ?demo=1 -> pré-remplit / bypass léger
        ctx = {
            "demo": request.GET.get("demo") == "1",
        }
        return render(request, "store/bonus_submit.html", ctx)

    # POST
    email = (request.POST.get("email") or "").strip()
    order_ref = (request.POST.get("order_ref") or "").strip()
    external = request.POST.get("is_external") == "on"
    text_input = (request.POST.get("text_input") or "").strip()

    # Validation basique
    if not email:
        return render(request, "store/bonus_submit.html", {"error": "Merci d’indiquer votre email d’achat.", "prefill": request.POST})

    if external:
        ok = validate_external_email(email)
        if not ok:
            return render(
                request, "store/bonus_submit.html",
                {"error": "L’email indiqué n’est pas reconnu parmi les achats partenaires.", "prefill": request.POST}
            )
    else:
        if not order_ref:
            return render(request, "store/bonus_submit.html", {"error": "Merci d’indiquer votre référence de commande.", "prefill": request.POST})
        ok = validate_internal_order_ref(order_ref, email)
        if not ok:
            return render(
                request, "store/bonus_submit.html",
                {"error": "Référence de commande invalide ou non trouvée pour cet email.", "prefill": request.POST}
            )

    if not text_input and not request.FILES.get("doc_file"):
        return render(request, "store/bonus_submit.html", {"error": "Merci de fournir votre texte (3 pages) ou un fichier.", "prefill": request.POST})

    # TODO: Enregistrer en BD (un modèle BonusSubmission ?)
    # Exemple minimal: envoyer un email interne + accusé client
    sent_ok = True
    try:
        # Email interne (vers contact@…)
        admin_to = getattr(settings, "SERVER_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if admin_to:
            body = f"""Nouvelle soumission Bonus Kit:
Email: {email}
Externe: {external}
Réf: {order_ref or '(externe)'}
Texte: {(text_input[:500] + '...') if len(text_input)>500 else text_input or '(via fichier)'}
"""
            EmailMessage(
                subject="Bonus Kit - Nouvelle soumission",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[admin_to],
            ).send(fail_silently=False)

        # Accusé client
        send_mail(
            subject="Nous avons bien reçu votre demande (Bonus - Audit Sans Peur)",
            message="Merci ! Nous analyserons votre texte (ou fichier) et reviendrons vers vous.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        sent_ok = False

    # Redirection Merci
    qs = f"?email={email}&ok={'1' if sent_ok else '0'}"
    return redirect(reverse("store:bonus_thanks") + qs)

def bonus_kit_thanks(request):
    email = request.GET.get("email")
    sent_ok = request.GET.get("ok") == "1"
    return render(request, "store/bonus_thanks.html", {"email": email, "sent_ok": sent_ok})

# -----------------------------
# BONUS: Kit de préparation
# -----------------------------
import re
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseBadRequest
from django.core.mail import send_mail, EmailMessage
from django.conf import settings

ORDER_REF_RE = re.compile(r"^SC[A-Z0-9]{5,}$", re.I)  # ex: SCD8LJ

def validate_internal_order_ref(order_ref: str, email: str) -> bool:
    """
    TODO: remplace par une vraie vérif en BD (ex: Order.objects.filter(...).exists()).
    Ici: on 'mock' : accepte une ref au format SCxxxxx et email non-vide.
    """
    if not email or not ORDER_REF_RE.match(order_ref or ""):
        return False
    return True

def validate_external_email(email: str) -> bool:
    """
    TODO: remplace par une vraie vérif contre la liste des emails transmis par les partenaires.
    Ici: on 'mock' : on accepte tout email qui contient un '@'.
    """
    return bool(email and "@" in email)

def bonus_kit_landing(request):
    # Ta template existante (bouton Démarrer => vers start)
    return render(request, "store/bonus_landing.html")

def bonus_kit_start(request):
    """
    GET  => Affiche le formulaire de soumission (texte / fichiers, email, ref / externe).
    POST => Valide & traite, puis redirige vers 'merci'.
    """
    if request.method == "GET":
        # mode DEMO ?demo=1 -> pré-remplit / bypass léger
        ctx = {
            "demo": request.GET.get("demo") == "1",
        }
        return render(request, "store/bonus_submit.html", ctx)

    # POST
    email = (request.POST.get("email") or "").strip()
    order_ref = (request.POST.get("order_ref") or "").strip()
    external = request.POST.get("is_external") == "on"
    text_input = (request.POST.get("text_input") or "").strip()

    # Validation basique
    if not email:
        return render(request, "store/bonus_submit.html", {"error": "Merci d’indiquer votre email d’achat.", "prefill": request.POST})

    if external:
        ok = validate_external_email(email)
        if not ok:
            return render(
                request, "store/bonus_submit.html",
                {"error": "L’email indiqué n’est pas reconnu parmi les achats partenaires.", "prefill": request.POST}
            )
    else:
        if not order_ref:
            return render(request, "store/bonus_submit.html", {"error": "Merci d’indiquer votre référence de commande.", "prefill": request.POST})
        ok = validate_internal_order_ref(order_ref, email)
        if not ok:
            return render(
                request, "store/bonus_submit.html",
                {"error": "Référence de commande invalide ou non trouvée pour cet email.", "prefill": request.POST}
            )

    if not text_input and not request.FILES.get("doc_file"):
        return render(request, "store/bonus_submit.html", {"error": "Merci de fournir votre texte (3 pages) ou un fichier.", "prefill": request.POST})

    # TODO: Enregistrer en BD (un modèle BonusSubmission ?)
    # Exemple minimal: envoyer un email interne + accusé client
    sent_ok = True
    try:
        # Email interne (vers contact@…)
        admin_to = getattr(settings, "SERVER_EMAIL", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        if admin_to:
            body = f"""Nouvelle soumission Bonus Kit:
Email: {email}
Externe: {external}
Réf: {order_ref or '(externe)'}
Texte: {(text_input[:500] + '...') if len(text_input)>500 else text_input or '(via fichier)'}
"""
            EmailMessage(
                subject="Bonus Kit - Nouvelle soumission",
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[admin_to],
            ).send(fail_silently=False)

        # Accusé client
        send_mail(
            subject="Nous avons bien reçu votre demande (Bonus - Audit Sans Peur)",
            message="Merci ! Nous analyserons votre texte (ou fichier) et reviendrons vers vous.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        sent_ok = False

    # Redirection Merci
    qs = f"?email={email}&ok={'1' if sent_ok else '0'}"
    return redirect(reverse("store:bonus_thanks") + qs)

def bonus_kit_thanks(request):
    email = request.GET.get("email")
    sent_ok = request.GET.get("ok") == "1"
    return render(request, "store/bonus_thanks.html", {"email": email, "sent_ok": sent_ok})


def training_inquiry(request):
    return HttpResponse("Formulaire de demande Formation & Assistance (stub) — à remplacer par ta vue réelle.")
