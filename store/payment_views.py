import logging
from typing import Optional

from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from store.models import Order, Product
from store.forms import PaymentForm
from store.services import orange_money, cinetpay

logger = logging.getLogger(__name__)


PROVIDERS = {
    "orange": orange_money,
    "cinetpay": cinetpay,
}


def _compute_amount_xof(product: Product, tier_id: Optional[str]) -> int:
    # Ajuste ce calcul si tu as des tiers
    amount_xof = (
        getattr(product, "price_fcfa", None)
        or getattr(product, "price", None)
    )
    try:
        return int(amount_xof or 0)
    except Exception:
        return 0


def _get_product_for_slug(slug: str) -> Product:
    """
    Resolve product for given slug.
    - If slug matches a real product → return it
    - If slug is an alias like 'cinetpay' → fallback to first published product
    """
    try:
        return Product.objects.get(slug=slug, is_published=True)
    except Product.DoesNotExist:
        if slug in {"cinetpay", "default"}:
            p = Product.objects.filter(is_published=True).first()
            if p:
                return p
        # Re-raise Not Found
        from django.http import Http404
        raise Http404("No Product matches the given query.")


def start_checkout(request, slug):
    product = _get_product_for_slug(slug)
    provider_key = request.POST.get("provider", "cinetpay")
    tier_id = request.POST.get("tier_id")

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            amount_xof = _compute_amount_xof(product, tier_id)
            if amount_xof <= 0:
                messages.error(request, "Montant invalide.")
                return redirect("store:buy", slug=product.slug)

            order = Order.objects.create(
                product=product,
                tier_id=tier_id or None,
                amount_fcfa=amount_xof,
                currency="XOF",
                status="PENDING",
                email=cd["email"],
                first_name=cd.get("first_name") or "",
                last_name=cd.get("last_name") or "",
                phone=cd.get("phone") or "",
            )

            try:
                if provider_key == "orange":
                    redirect_url, external_ref = orange_money.create_checkout(
                        inquiry_id=order.id,
                        amount=order.amount_fcfa,
                        currency="XOF",
                        request=request,
                    )
                    # Aligner la ref provider (utilisée pour checks/retours)
                    order.provider_ref = external_ref
                    order.save(update_fields=["provider_ref"])
                    return redirect(redirect_url)
                else:
                    # CinetPay: utilise provider_ref auto et init_payment_auto
                    redirect_url = cinetpay.init_payment_auto(
                        order=order,
                        request=request,
                    )
                    return redirect(redirect_url)
            except Exception as e:
                messages.error(
                    request,
                    f"Erreur de paiement {provider_key}: {e}",
                )
                logger.exception(e)
        else:
            messages.error(request, "Formulaire invalide.")
    else:
        form = PaymentForm()

    return render(
        request,
        "store/buy_cinetpay.html",
        {
            "form": form,
            "product": product,
            "provider": provider_key,
            "tier": None,
        },
    )


def om_return(request):
    ref = request.GET.get("transaction_id") or request.GET.get("ref")
    if not ref:
        return redirect("store:buy", slug=request.GET.get("slug", ""))
    order = get_object_or_404(Order, provider_ref=ref)
    is_paid, provider_tx = orange_money.check_transaction_status(ref)
    if is_paid:
        order.mark_paid(provider="orange", provider_tx=provider_tx)
        # Marquer la session pour autoriser l'accès
        # à la page de téléchargement sécurisée
        request.session["order_email"] = order.email
        paid = set(request.session.get("paid_orders", []))
        paid.add(str(order.uuid))
        request.session["paid_orders"] = list(paid)
        # Email de fulfilment (liens ebook/bonus/ressources)
        try:
            from store.services.mailing import send_fulfilment_email
            order_ref = (
                order.provider_ref
                or order.cinetpay_payment_id
                or str(order.uuid)
            )
            send_fulfilment_email(
                to_email=order.email,
                order_ref=order_ref,
            )
        except Exception:
            logger.exception("[OM_RETURN] Erreur envoi email de fulfilment")
        messages.success(request, "Paiement confirmé avec succès ✅")
        try:
            return redirect("downloads:secure", order_uuid=order.uuid)
        except Exception:
            return redirect("store:payment_success", order_id=order.id)
    messages.error(request, "Le paiement n’a pas encore été confirmé.")
    return redirect("store:buy", slug=order.product.slug)


@csrf_exempt
def om_notify(request):
    payload = orange_money.verify_webhook(request)
    if not payload:
        return HttpResponse(status=400)

    ref = payload.get("transaction_id")
    status = payload.get("status", "")
    order = Order.objects.filter(provider_ref=ref).first()
    if not order:
        return HttpResponse(status=404)

    if orange_money.map_provider_status_to_paid(status):
        order.mark_paid(
            provider="orange",
            provider_tx=payload.get("provider_tx_id") or ref,
        )
        logger.info(f"[OM_NOTIFY] Paiement confirmé pour {ref}")
        # Email de fulfilment (liens ebook/bonus/ressources)
        try:
            from store.services.mailing import send_fulfilment_email
            order_ref = (
                order.provider_ref
                or order.cinetpay_payment_id
                or str(order.uuid)
            )
            send_fulfilment_email(
                to_email=order.email,
                order_ref=order_ref,
            )
        except Exception:
            logger.exception("[OM_NOTIFY] Erreur envoi email de fulfilment")

    return JsonResponse({"ok": True})


def om_mock_checkout(request):
    """
    Page locale simulant le checkout Orange Money en sandbox.
    Permet de cliquer pour confirmer le paiement (redirige vers om_return).
    """
    tx = request.GET.get("transaction_id") or ""
    if not tx:
        return HttpResponse("transaction_id manquant", status=400)
    return render(request, "store/om_mock_checkout.html", {"tx": tx})


def cinetpay_mock_checkout(request):
    """
    Page locale simulant le checkout CinetPay (mode mock).
    Par défaut, redirige immédiatement vers la vue
    de retour avec le tx.
    """
    tx = request.GET.get("transaction_id") or ""
    if not tx:
        return HttpResponse("transaction_id manquant", status=400)
    logger.info(f"[CINETPAY MOCK] checkout page for tx={tx}")
    # Redirection immédiate vers la vue de retour
    # (peut être remplacée par une page avec bouton)
    from django.urls import reverse
    return redirect(f"{reverse('store:cinetpay_return')}?transaction_id={tx}")
