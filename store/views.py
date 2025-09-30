# store/views.py
import hashlib
import hmac
import logging
import os
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage, send_mail
from django.db.models import Prefetch
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

import store.services.cinetpay as cinetpay
from downloads.models import DownloadableAsset
from store.content.faqs import FAQ_ITEMS

from .forms import CheckoutForm, KitInquiryForm, TrainingInquiryForm
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

logger = logging.getLogger("cinetpay")

# ---- Pages ----


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_published=True)
    media = MediaAsset.objects.filter(product=product)
    proofs = product.social_proofs_json or []
    standard_tier = OfferTier.objects.filter(product=product, kind="STANDARD").first()

    # Seed tableau d'analyse (extrait)
    rows_ebook = SEED_IRREGULARITIES.get(slug, [])

    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "media": media,
            "faqs": FAQ_ITEMS,  # <-- injection FAQ centralisée
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


@require_http_methods(["GET", "POST"])
def kit_inquiry(request):
    MAX_ATTACH_TOTAL = 15 * 1024 * 1024  # 15 Mo
    MAX_FILES = 10
    MAX_FILE_SIZE = 10 * 1024 * 1024
    ALLOWED_EXTS = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".gif"]
    INQUIRY_TO = ["contact@ton-domaine.com"]

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
            # Email
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
                logger.exception("Erreur d'envoi email (kit)")
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
MAX_FILES = 10  # Nouvelle constante pour le nombre de fichiers
MAX_FILE_SIZE = 10 * 1024 * 1024  # Nouvelle constante pour la taille maximale d'un fichier
ALLOWED_EXTS = [
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
]  # Nouvelle constante pour les extensions autorisées


def total_size(files):
    return sum(getattr(f, "size", 0) for f in files)


INQUIRY_TO = ["contact@ton-domaine.com"]  # à adapter
MAX_ATTACH_TOTAL = 15 * 1024 * 1024  # 15 Mo


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
                    subject=subject, body=body, to=["contact@exemple.com"], reply_to=[data["email"]]
                )
                # … attach if needed …
                email.send(fail_silently=False)
                messages.success(
                    request,
                    "Merci, votre demande a bien été envoyée. Nous vous contactons sous 24–48 h.",
                )
            except Exception:
                logger.exception("Erreur d'envoi email")
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
    # Page simple de remerciement
    return render(request, "store/training_inquiry_success.html")


def examples(request):
    """Page /exemples/ : cadre central avec carrousel 'Exemples' par défaut."""
    product = Product.objects.filter(is_published=True).first()
    slides = ExampleSlide.objects.filter(product=product) if product else []
    return render(request, "store/examples.html", {"product": product, "slides": slides})


# ---- Partial HTMX : tableau selon version ----
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
            # Montant/devise fixés côté serveur uniquement
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
                provider_ref=f"ORDER-{uuid.uuid4().hex}",  # ⬅️ transaction_id stable
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
        # Suppose que downloads.models.Asset existe et a un slug
        asset = DownloadableAsset.objects.filter(slug=product.download_slug).first()
        if asset:
            download_url = asset.get_absolute_url() if hasattr(asset, "get_absolute_url") else None
    return render(
        request, "store/payment_success.html", {"order": order, "download_url": download_url}
    )


# --- Paiement CinetPay sécurisé ---
# Sécurité Go/No-Go : Montant et devise toujours fixés côté serveur (jamais depuis le client)
import json
import logging

from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from store.models import Payment

try:
    from store.models import PaymentEvent  # optional
except Exception:
    PaymentEvent = None

import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from store.services.cinetpay import payment_check, verify_signature

# deliver_ebook is defined locally below, do not import


def _sigdebug(header_name, sig, raw):
    """Log non-sensitive signature diag when CINETPAY_SIG_DEBUG=1."""
    if os.getenv("CINETPAY_SIG_DEBUG") != "1":
        return
    logger = logging.getLogger(__name__)
    secret = os.getenv("CINETPAY_WEBHOOK_SECRET") or ""
    logger.warning(
        "[SIGDEBUG] header=%s provided[:24]=%s body_len=%d body_sha256=%s secret_sha256[:24]=%s",
        header_name,
        str(sig)[:24],
        len(raw or b""),
        hashlib.sha256(raw or b"").hexdigest(),
        hashlib.sha256(secret.encode()).hexdigest()[:24],
    )


@require_POST
def start_checkout(request, product_slug, tier_id):
    """
    Crée un Payment et redirige vers l'URL de paiement CinetPay (server-side only).
    Montant/devise toujours fixés côté serveur (jamais depuis le client).
    """
    import uuid

    from .models import OfferTier, Product

    product = get_object_or_404(Product, slug=product_slug, is_published=True)
    tier = get_object_or_404(OfferTier, id=tier_id, product=product)
    email = request.POST.get("email")
    if not email:
        return JsonResponse({"error": "Email requis"}, status=400)
    amount = tier.price_fcfa or product.price_fcfa  # Jamais depuis le client
    order_id = uuid.uuid4().hex[:32]
    payment = Payment.objects.create(
        order_id=order_id,
        amount=amount,
        currency="XOF",  # Jamais depuis le client
        email=email,
        status="INIT",
    )
    PaymentEvent.objects.create(
        payment=payment, kind="INIT", payload={"amount": amount, "email": email}
    )
    try:
        pay_url = cinetpay.init_payment_auto(order=payment, request=request)
    except Exception as e:
        payment.status = "FAILED"
        payment.save(update_fields=["status"])
        PaymentEvent.objects.create(payment=payment, kind="ERROR", payload={"error": str(e)})
        return JsonResponse({"error": "Erreur lors de l'initialisation du paiement."}, status=500)
    payment.status = "PENDING"
    payment.save(update_fields=["status"])
    PaymentEvent.objects.create(payment=payment, kind="PENDING", payload={"pay_url": pay_url})
    return JsonResponse({"redirect_url": pay_url})


def payment_return(request):
    transaction_id = request.GET.get("transaction_id")
    if not transaction_id:
        return HttpResponseBadRequest("Missing transaction_id parameter.")
    order = get_object_or_404(Order, transaction_id=transaction_id)
    # Enregistrer dans la session
    request.session["order_email"] = order.email
    paid = set(request.session.get("paid_orders", []))
    paid.add(str(order.uuid))
    request.session["paid_orders"] = list(paid)
    return redirect("downloads:secure", order_uuid=order.uuid)


@csrf_exempt
@require_POST
def cinetpay_callback(request):
    """
    Secure CinetPay webhook:
    - HMAC signature over raw request.body
    - idempotence (no double delivery)
    - server-to-server payment_check before delivery
    - safe 200 responses to avoid provider retries
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

    # 2) Parse JSON
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    order_id = (
        payload.get("transaction_id") or payload.get("cpm_trans_id") or payload.get("order_id")
    )
    if not order_id:
        return HttpResponseBadRequest("Missing order_id")

    # 3) Idempotence + server-to-server check
    with transaction.atomic():
        try:
            payment = Payment.objects.select_for_update().get(order_id=order_id)
        except Payment.DoesNotExist:
            logging.getLogger(__name__).error("Webhook for unknown order_id=%s", order_id)
            # Return 200 to avoid endless retries; investigation via logs
            return JsonResponse({"ok": False, "reason": "unknown_order"}, status=200)

        # Optional raw trace (do not block flow if it fails)
        if PaymentEvent:
            try:
                PaymentEvent.objects.create(payment=payment, kind="WEBHOOK", payload=payload)
            except Exception:
                logging.getLogger(__name__).exception(
                    "Failed to persist PaymentEvent for %s", order_id
                )

        # Idempotence: already paid → no re-delivery
        if getattr(payment, "status", None) == "PAID":
            return JsonResponse({"ok": True, "idempotent": True}, status=200)

        # Optional consistency checks if payload contains amount/currency
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
            pass  # never block on logging

        # Server-to-server validation
        ok, provider_tx_id = payment_check(order_id)
        if not ok:
            # Mark as failed but return 200 to avoid retries loops
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
                    logging.getLogger(__name__).exception(
                        "Failed to persist CHECK_FAIL for %s", order_id
                    )
            return JsonResponse({"ok": False, "reason": "check_failed"}, status=200)

        # Mark paid, then deliver exactly once
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
            deliver_ebook(payment)  # unique download link + email
        except Exception as e:
            logging.getLogger(__name__).exception("Delivery error for %s: %s", order_id, e)
            # Return 200 to prevent provider retries
            return JsonResponse({"ok": True, "delivered": False}, status=200)

    return JsonResponse({"ok": True, "delivered": True}, status=200)


def deliver_ebook(payment):
    """
    Génère un lien de téléchargement unique et expirable, envoie l'e-mail, journalise l'event.
    """
    from django.urls import reverse

    from store.models import DownloadToken, Order

    order = Order.objects.filter(provider_ref=payment.order_id).first()
    if not order:
        return
    # Générer ou récupérer le DownloadToken
    token_obj, _ = DownloadToken.objects.get_or_create(order=order)
    # Construire l'URL sécurisée
    base_url = settings.CINETPAY_RETURN_URL.rstrip("/")
    download_url = f"{base_url}" + reverse("downloads:secure_token", args=[str(token_obj.token)])
    # Envoi e-mail confirmation
    subject = "Votre lien de téléchargement AuditShield"
    message = (
        f"Merci pour votre achat !\n\n"
        f"Téléchargez votre ebook ici (valable 72h) : {download_url}\n\n"
        f"Ceci est un lien personnel et temporaire."
    )
    send_mail(subject, message, None, [payment.email])
    PaymentEvent.objects.create(
        payment=payment, kind="DELIVERED", payload={"download_url": download_url}
    )


@csrf_exempt
@require_POST
def payment_notify(request):
    import json

    from store.services import deliver_order

    try:
        # Parse JSON
        try:
            payload = json.loads(request.body.decode())
        except Exception:
            logger.warning("[CinetPay][notify] Invalid JSON")
            return JsonResponse({"detail": "Invalid JSON"}, status=400)
        # Masquage des clés sensibles
        masked = {k: ("***" if "key" in k else v) for k, v in payload.items()}
        logger.info(f"[CinetPay][notify] Payload: {masked}")
        transaction_id = payload.get("transaction_id")
        if not transaction_id:
            return JsonResponse({"detail": "Missing transaction_id"}, status=400)
        # Retrouver l'Order
        order = Order.objects.filter(provider_ref=transaction_id).first()
        if not order:
            logger.warning(
                f"[CinetPay][notify] Order not found for transaction_id={transaction_id}"
            )
            return JsonResponse({"detail": "Order not found"}, status=404)
        # Re-check côté serveur
        try:
            check = cinetpay.safe_check(transaction_id)
        except Exception as e:
            logger.error(f"[CinetPay][notify] CinetPay check error: {str(e)}")
            return JsonResponse({"detail": "CinetPay check error"}, status=502)
        status = (check.get("data") or {}).get("status", "")
        logger.info(f"[CinetPay][notify] Order {order.id} - check status: {status}")
        if status in ("ACCEPTED", "SUCCESS", "PAID"):
            order.status = Order.PAID
            order.save(update_fields=["status"])
            deliver_order(order)
            send_download_email(order)
        elif status in ("REFUSED", "CANCELED", "FAILED"):
            order.status = Order.FAILED
            order.save(update_fields=["status"])
        # Sinon, laisser PENDING
        return JsonResponse({"detail": "OK"})
    except Exception as e:
        logger.error(f"[CinetPay][notify] Unexpected error: {str(e)}")
        return JsonResponse({"detail": "Unexpected error"}, status=500)


# Webhook HMAC (structure + check API si besoin)
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

    # Option recommandée : re-checker côté API avant de livrer
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

    - mode=carousel → slides "Exemples d'irrégularités"
    - mode=table    → tableaux (catégories IrregularityCategory) 5 lignes max
    - mode=prelim   → carrousel de tables d'analyses préliminaires (5 lignes max)
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

    # par défaut: carousel des ExampleSlide
    slides = ExampleSlide.objects.filter(product=product).order_by("order", "id") if product else []
    return render(request, "store/partials/examples_block_carousel.html", {"slides": slides})


# Page dédiée SEO/partage pour les analyses préliminaires
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
            # Suppose que get_absolute_url existe, sinon adapte ici
            download_url = asset.get_absolute_url() if hasattr(asset, "get_absolute_url") else None
    if download_url:
        subject = f"Votre ebook : {product.title}"
        message = f"Bonjour {order.first_name},\n\nMerci pour votre achat !\n\nVous pouvez télécharger votre ebook ici : {download_url}\n\nCe lien est personnel et réservé à votre usage.\n\nBonne lecture !\nL'équipe AuditShield"
        send_mail(subject, message, None, [order.email])
    else:
        subject = "Votre achat sur AuditShield"
        message = f"Bonjour {order.first_name},\n\nMerci pour votre achat ! Nous vous enverrons votre lien de téléchargement dès que possible.\n\nL'équipe AuditShield"
        send_mail(subject, message, None, [order.email])


# ---- Nouvelles vues CinetPay sécurisées ----


def _cinetpay_secret_bytes():
    """Secret prioritaire = SECRET_KEY dédié CinetPay ; fallback = API_KEY (si pas de secret distinct fourni)"""
    from django.conf import settings

    secret = settings.CINETPAY_SECRET_KEY or settings.CINETPAY_API_KEY or ""
    return secret.encode("utf-8")


def cinetpay_return(request):
    """Page succès client"""
    # TODO: lire les query params pour remonter un message ou l'order_id si besoin
    return HttpResponse("Paiement réussi. Merci.")


def cinetpay_cancel(request):
    """Page annulation client"""
    return HttpResponse("Paiement annulé.")


@csrf_exempt
def cinetpay_notify(request):
    """
    Webhook CinetPay sécurisé avec vérification HMAC SHA-256
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Méthode non autorisée")

    raw = request.body or b""
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("JSON invalide")

    # Signature (adaptable selon l'entête exact utilisé par CinetPay)
    received_sig = (
        request.headers.get("X-Signature")
        or request.headers.get("x-signature")
        or data.get("signature", "")
    )
    expected_sig = hmac.new(_cinetpay_secret_bytes(), raw, hashlib.sha256).hexdigest()

    # Debug temporaire
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        f"[DEBUG] Received sig: {received_sig[:20]}... | Expected sig: {expected_sig[:20]}... | Secret: {_cinetpay_secret_bytes()[:10]}..."
    )

    if not received_sig or not hmac.compare_digest(received_sig, expected_sig):
        # log même si signature invalide
        PaymentWebhookLog.objects.create(
            order_ref=str(data.get("transaction_id") or data.get("custom") or ""),
            status=str(data.get("status") or ""),
            signature=str(received_sig or ""),
            raw_body=raw.decode("utf-8", "ignore"),
            processed=False,
            http_status=400,
        )
        return HttpResponseBadRequest("Signature invalide")

    order_ref = str(data.get("transaction_id") or data.get("custom") or "")
    status = str(data.get("status") or "")

    # Idempotence simple : si on a déjà un log processed=True pour cet order_ref et status SUCCESS, on ne retrait pas
    already_ok = PaymentWebhookLog.objects.filter(
        order_ref=order_ref, status__iexact="SUCCESS", processed=True
    ).exists()

    # TODO : si tu as un modèle Payment, c'est ici que tu:
    #  1) récupères la commande par order_ref
    #  2) vérifies le montant, la devise, etc.
    #  3) mets à jour le statut payé/échoué
    #  4) déclenches l'accès au téléchargement si succès

    log = PaymentWebhookLog.objects.create(
        order_ref=order_ref,
        status=status.upper(),
        signature=str(received_sig),
        raw_body=raw.decode("utf-8", "ignore"),
        processed=False,
        http_status=200,
    )

    if status.upper() == "SUCCESS" and not already_ok:
        # Marque processed=True (idempotence basique)
        log.processed = True
        log.save(update_fields=["processed"])

    return HttpResponse("OK")
