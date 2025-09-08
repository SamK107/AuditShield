# store/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# --- CINETPAY FLOW ---
from django.views.decorators.http import require_POST

from .models import Product, OfferTier, ExampleSlide, MediaAsset, Order, DownloadToken, IrregularityCategory
import store.services.cinetpay as cinetpay
import uuid, os, hmac, hashlib
from .models import Product, ExampleSlide, IrregularityRow
from django.db.models import Prefetch  # <— AJOUT ICI
from .models import PreliminaryTable, PreliminaryRow
import logging
logger = logging.getLogger("cinetpay")

from .forms import CheckoutForm
from django.urls import reverse
from django.core.mail import send_mail
from downloads.models import DownloadableAsset
from .seeds.ebook_irregularities import SEED_IRREGULARITIES  # <-- add

# ---- Pages ----

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_published=True)
    media = MediaAsset.objects.filter(product=product)
    faqs = product.faq_json or []
    proofs = product.social_proofs_json or []
    standard_tier = OfferTier.objects.filter(product=product, kind="STANDARD").first()

    # Seed tableau d’analyse (extrait)
    rows_ebook = SEED_IRREGULARITIES.get(slug, [])

    return render(request, "store/product_detail.html", {
        "product": product,
        "media": media,
        "faqs": faqs,
        "proofs": proofs,
        "standard_tier": standard_tier,
        "rows_ebook": rows_ebook,  # <-- add
    })

def offers(request):
    product = Product.objects.filter(is_published=True).first()
    tiers = OfferTier.objects.filter(product=product) if product else []
    return render(request, "store/offers.html", {"product": product, "tiers": tiers})

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
    rows = IrregularityRow.objects.filter(product=product, version=version).order_by("order")[:5] if product else []
    return render(request, "store/partials/irregularities_table.html", {"rows": rows, "version": version})


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
            tier_id = data.get("tier_id") or (standard_tier.id if standard_tier else None)
            if not tier_id:
                return render(request, "store/payment_error.html", {"message": "Offre invalide."}, status=400)
            tier = get_object_or_404(OfferTier, id=tier_id, product=product)
            transaction_id = uuid.uuid4().hex[:24].upper()
            order = Order.objects.create(
                product=product,
                tier_id=tier.id,
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone=data["phone"],
                amount_fcfa=tier.price_fcfa or product.price_fcfa,
                status="PENDING",
                cinetpay_payment_id=transaction_id,
                provider_ref=transaction_id,
                currency="XOF",
            )
            try:
                payment_url = cinetpay.init_payment_auto(order=order, request=request)
            except Exception as e:
                order.delete()
                return render(request, "store/payment_error.html", {"message": "Erreur lors de l'initialisation du paiement."}, status=500)
            return redirect(payment_url)
    else:
        form = CheckoutForm(initial={"tier_id": standard_tier.id if standard_tier else None})
    return render(request, "store/checkout.html", {"form": form, "product": product, "tier": tier or standard_tier})


def payment_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    product = order.product
    download_url = None
    if product.download_slug:
        # Suppose que downloads.models.Asset existe et a un slug
        asset = DownloadableAsset.objects.filter(slug=product.download_slug).first()
        if asset:
            download_url = asset.get_absolute_url() if hasattr(asset, "get_absolute_url") else None
    return render(request, "store/payment_success.html", {"order": order, "download_url": download_url})

def payment_return(request):
    """Page de retour après paiement (ne valide rien, juste info utilisateur)."""
    return render(request, "store/payment_return.html")


@csrf_exempt
@require_POST
def payment_notify(request):
    import json
    from django.views.decorators.csrf import csrf_exempt
    from django.http import JsonResponse
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
            logger.warning(f"[CinetPay][notify] Order not found for transaction_id={transaction_id}")
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
    "cpm_site_id", "cpm_trans_id", "cpm_trans_date", "cpm_amount", "cpm_currency",
    "signature", "payment_method", "cel_phone_num", "cpm_phone_prefixe", "cpm_language",
    "cpm_version", "cpm_payment_config", "cpm_page_action", "cpm_custom",
    "cpm_designation", "cpm_error_message",
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
    status_ok = (res.get("code") == "00" and res.get("data", {}).get("status") == "ACCEPTED")

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
    orders = Order.objects.filter(email=request.user.email).order_by('-created_at')
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
        subject = f"Votre achat sur AuditShield"
        message = f"Bonjour {order.first_name},\n\nMerci pour votre achat ! Nous vous enverrons votre lien de téléchargement dès que possible.\n\nL'équipe AuditShield"
        send_mail(subject, message, None, [order.email])

