# store/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Product, OfferTier, ExampleSlide, MediaAsset, Order, DownloadToken
from .services import cinetpay
import uuid, os, hmac, hashlib

# ---- Pages ----

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_published=True)
    media = MediaAsset.objects.filter(product=product)
    faqs = product.faq_json or []
    proofs = product.social_proofs_json or []
    return render(request, "store/product_detail.html", {
        "product": product, "media": media, "faqs": faqs, "proofs": proofs
    })

def offers(request):
    product = Product.objects.filter(is_published=True).first()
    tiers = OfferTier.objects.filter(product=product) if product else []
    return render(request, "store/offers.html", {"product": product, "tiers": tiers})

def examples(request):
    product = Product.objects.filter(is_published=True).first()
    slides = ExampleSlide.objects.filter(product=product) if product else []
    return render(request, "store/examples.html", {"slides": slides, "product": product})

# ---- Paiement ----

@require_http_methods(["POST"])
def buy(request, slug):
    product = get_object_or_404(Product, slug=slug, is_published=True)
    email = request.POST.get("email") or "client@example.com"

    order = Order.objects.create(
        product=product,
        email=email,
        amount_fcfa=product.price_fcfa,
        status=Order.PENDING,
        cinetpay_payment_id=uuid.uuid4().hex[:24].upper(),
    )

    pay_url = cinetpay.init_payment_auto(order=order, request=request)
    return redirect(pay_url)

@require_http_methods(["GET", "POST"])
def payment_return(request):
    # Supporte le mock (?status=success&order=<uuid>) et/ou transaction_id réel
    status = request.GET.get("status")
    order_id = request.GET.get("order")
    tx_id = request.GET.get("transaction_id")
    order = None
    if order_id:
        order = Order.objects.filter(order_id=order_id).first()
    elif tx_id:
        order = Order.objects.filter(cinetpay_payment_id=tx_id).first()

    if not order:
        return render(request, "store/thank_you.html", {"ok": False, "message": "Commande introuvable."})

    if status == "success":  # chemin mock
        order.status = Order.PAID
        order.save(update_fields=["status"])
        token, _ = DownloadToken.objects.get_or_create(order=order)
        return render(request, "store/thank_you.html", {"ok": True, "order": order, "token": token})

    if order.status == Order.PAID:
        token, _ = DownloadToken.objects.get_or_create(order=order)
        return render(request, "store/thank_you.html", {"ok": True, "order": order, "token": token})

    return render(request, "store/thank_you.html", {"ok": False, "message": "Paiement en cours de confirmation…"})

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
