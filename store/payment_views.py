import json
import logging
from typing import Optional

from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from store.models import Order, Product, ClientInquiry, Payment
from store.forms import PaymentForm
from store.services import orange_money, cinetpay, payments

logger = logging.getLogger(__name__)


PROVIDERS = {
    "orange": orange_money,
    "cinetpay": cinetpay,
}


def _is_kit_complete_order(order: Order) -> bool:
    """
    Détermine si un Order est pour le Kit complet personnalisé.
    Un Order est pour le Kit complet s'il est lié à un ClientInquiry de type KIT.
    """
    try:
        inquiry = getattr(order, "inquiries", None)
        if inquiry:
            # Si l'Order a une relation inquiries (via related_name)
            inquiry = inquiry.first()
            if inquiry and inquiry.kind == ClientInquiry.KIND_KIT:
                return True
        # Alternative: chercher via ClientInquiry.order
        inquiry = ClientInquiry.objects.filter(
            order=order, kind=ClientInquiry.KIND_KIT
        ).first()
        if inquiry:
            return True
        # Vérifier aussi via le product slug ou tier
        if order.product and order.product.slug == "audit-sans-peur":
            # Si le tier est de type KIT
            if order.tier_id:
                from store.models import OfferTier
                tier = OfferTier.objects.filter(id=order.tier_id).first()
                if tier and tier.kind == "KIT":
                    return True
        return False
    except Exception:
        logger.exception(
            f"[_is_kit_complete_order] Erreur pour order {order.id}"
        )
        return False


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
    - If slug is an alias like 'cinetpay-orange' → fallback to first published product
    """
    try:
        return Product.objects.get(slug=slug, is_published=True)
    except Product.DoesNotExist:
        if slug in {"cinetpay-orange", "cinetpay", "default"}:
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

    # Debug logging
    logger.info(f"[start_checkout] Request method: {request.method}")
    logger.info(f"[start_checkout] Product slug: {slug}")
    logger.info(f"[start_checkout] Provider key: {provider_key}")
    logger.info(f"[start_checkout] POST data: {dict(request.POST)}")

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
                if provider_key in ("orange", "orange_money_ml"):
                    # Utiliser la nouvelle API réelle Orange Money WebPay Dev
                    # Conforme au guide officiel Orange Money
                    result = orange_money.create_payment_request(order, request=request)
                    payment_url = result["payment_url"]
                    pay_token = result.get("pay_token")
                    notif_token = result.get("notif_token")
                    order_id = result["order_id"]
                    
                    # Log pour debug
                    logger.info(f"[OM][start_checkout] API response - payment_url: {payment_url}, pay_token: {pay_token}")
                    
                    # Enregistrer la référence provider
                    order.provider_ref = order_id
                    if pay_token:
                        # Stocker le pay_token dans cinetpay_payment_id (legacy field)
                        # Cela permettra de retrouver l'Order depuis le webhook
                        order.cinetpay_payment_id = pay_token
                    order.save(update_fields=["provider_ref", "cinetpay_payment_id"])
                    
                    # Stocker la réponse brute dans un Payment si le modèle existe
                    try:
                        payment = Payment.objects.create(
                            order_id=order_id,
                            provider_tx_id=pay_token or order_id,
                            status="PENDING",
                            amount=int(order.amount_fcfa),
                            currency="XOF",
                            email=order.email,
                        )
                        # Stocker la réponse brute (inclut notif_token) si possible
                        if hasattr(payment, 'raw_response'):
                            payment.raw_response = result.get("raw_response", {})
                            payment.save(update_fields=["raw_response"])
                    except Exception as e:
                        logger.warning(
                            f"[OM][start_checkout] Erreur création Payment: {e}"
                        )
                    
                    # Log notif_token pour traçabilité
                    if notif_token:
                        logger.info(
                            f"[OM][start_checkout] notif_token: {notif_token}"
                        )
                    
                    # Rediriger vers l'URL de paiement Orange Money
                    logger.info(f"[OM][start_checkout] Redirection vers Orange Money: {payment_url}")
                    return redirect(payment_url)
                else:
                    # CinetPay: utilise provider_ref auto et init_payment_auto
                    redirect_url = cinetpay.init_payment_auto(
                        order=order,
                        request=request,
                    )
                    return redirect(redirect_url)
            except orange_money.OrangeMoneyAuthError as e:
                logger.error(f"[OM][start_checkout] Erreur OAuth: {e}")
                messages.error(
                    request,
                    "Erreur d'authentification Orange Money. Veuillez réessayer plus tard."
                )
                # Supprimer l'ordre créé si l'authentification échoue
                order.delete()
            except orange_money.OrangeMoneyAPIError as e:
                # Log détaillé de l'erreur API avec status_code et response_data
                logger.error(
                    f"[OM][start_checkout] Erreur API (status={getattr(e, 'status_code', 'N/A')}): {e}"
                )
                if hasattr(e, 'response_data') and e.response_data:
                    logger.error(
                        f"[OM][start_checkout] Response data: {json.dumps(e.response_data, ensure_ascii=False)}"
                    )
                
                # Message utilisateur convivial selon le code d'erreur
                status_code = getattr(e, 'status_code', None)
                if status_code and status_code != 201:
                    messages.error(
                        request,
                        f"Le service de paiement Orange Money a retourné une erreur (code {status_code}). "
                        f"Veuillez vérifier vos informations et réessayer."
                    )
                else:
                    messages.error(
                        request,
                        f"Erreur lors de l'initialisation du paiement Orange Money. "
                        f"Veuillez réessayer ou contacter le support."
                    )
                # Supprimer l'ordre créé si l'API échoue
                order.delete()
            except Exception as e:
                messages.error(
                    request,
                    f"Erreur de paiement {provider_key}: {e}",
                )
                logger.exception(e)
                # Supprimer l'ordre créé en cas d'erreur inattendue
                order.delete()
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
    """
    Page de retour après l'interface Orange Money.
    La vraie confirmation de paiement se fait via om_notify.
    Redirige vers la page appropriée selon le type de commande.
    """
    order_id = request.GET.get("order_id") or request.GET.get("transaction_id")
    
    if not order_id:
        # Si pas de paramètre, on essaie de trouver via Payment ou Order
        return render(request, "store/payment_return.html", {"order_id": None})
    
    # Chercher l'Order via provider_ref (order_id)
    order = Order.objects.filter(provider_ref=order_id).first()
    
    if not order:
        logger.warning(f"[OM][return] Order introuvable pour order_id={order_id}")
        return render(
            request,
            "store/payment_return.html",
            {"order_id": order_id, "error": "Commande introuvable"},
        )
    
    # Si le paiement est confirmé, rediriger selon le type de commande
    if order.status == Order.PAID:
        if _is_kit_complete_order(order):
            # Pour le Kit complet : chercher ou créer KitOrder et rediriger
            try:
                from store.models import KitOrder
                kit_order = KitOrder.objects.filter(order=order).first()
                if kit_order:
                    return redirect(
                        "store:kit_payment_success",
                        tracking_id=kit_order.tracking_id,
                    )
                # Si pas encore créé, créer maintenant
                from store.services.kit_orders import (
                    create_kit_order_from_payment,
                    send_kit_order_confirmation_email,
                )
                kit_order = create_kit_order_from_payment(order)
                send_kit_order_confirmation_email(kit_order)
                return redirect(
                    "store:kit_payment_success",
                    tracking_id=kit_order.tracking_id,
                )
            except Exception:
                logger.exception("[OM][return] Erreur création KitOrder, fallback")
                # Fallback vers l'ancienne page
                inquiry = ClientInquiry.objects.filter(
                    order=order, kind=ClientInquiry.KIND_KIT
                ).first()
                if inquiry and inquiry.selected_tier_code:
                    return redirect(
                        f"{reverse('store:kit_inquiry_success')}?tier={inquiry.selected_tier_code}&paid=1"
                    )
                return redirect(f"{reverse('store:kit_inquiry_success')}?paid=1")
        else:
            # Pour l'ebook : rediriger vers la page de téléchargement
            try:
                return redirect("downloads:secure", order_uuid=order.uuid)
            except Exception:
                pass
    
    # Sinon, afficher la page de statut
    context = {
        "order_id": order_id,
        "order": order,
        "is_paid": order.status == Order.PAID,
    }
    
    return render(request, "store/payment_return.html", context)


@csrf_exempt
def om_notify(request):
    """
    Notification serveur Orange Money (notif_url).
    """
    if request.method == "GET":
        return HttpResponse("OK", status=200)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        logger.error("[OM][notify] Payload JSON invalide")
        return HttpResponse(status=400)

    logger.info(f"[OM][notify] payload={data}")

    status = data.get("status", "").upper()
    notif_token = data.get("notif_token")
    txnid = data.get("txnid") or data.get("transaction_id")
    order_id = data.get("order_id")  # order_id généré par create_checkout

    if not order_id:
        logger.warning("[OM][notify] order_id manquant dans le payload")
        return HttpResponse(status=400)

    # Retrouver le Payment ou l'Order via order_id (provider_ref)
    order = Order.objects.filter(provider_ref=order_id).first()
    
    if not order:
        logger.warning(f"[OM][notify] Payment/Order introuvable pour order_id={order_id}")
        return HttpResponse(status=404)

    # Optionnel : vérifier notif_token si on le stocke dans le Payment
    # Pour l'instant, on skip cette vérification

    # Mettre à jour le statut
    if status == "SUCCESS" or orange_money.map_provider_status_to_paid(status):
        try:
            order.mark_paid(provider="orange", provider_tx=txnid or order_id)
            logger.info(f"[OM][notify] Paiement confirmé pour order_id={order_id}")
            
            # Gérer le Kit complet : créer KitOrder et envoyer email
            if _is_kit_complete_order(order):
                try:
                    from store.services.kit_orders import (
                        create_kit_order_from_payment,
                        send_kit_order_confirmation_email,
                    )
                    kit_order = create_kit_order_from_payment(order)
                    send_kit_order_confirmation_email(kit_order)
                    logger.info(
                        f"[OM][notify] KitOrder créé: {kit_order.tracking_id}"
                    )
                except Exception:
                    logger.exception(
                        "[OM][notify] Erreur création KitOrder"
                    )
            else:
                # Déclencher fulfillment pour l'ebook
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
                    logger.exception("[OM][notify] Erreur envoi email de fulfilment")
        except Exception:
            logger.exception(f"[OM][notify] Erreur mark_paid pour order_id={order_id}")
    else:
        # Paiement échoué
        try:
            order.status = Order.FAILED
            order.save(update_fields=["status"])
            logger.info(f"[OM][notify] Paiement échoué pour order_id={order_id}, status={status}")
        except Exception:
            logger.exception(f"[OM][notify] Erreur mark_failed pour order_id={order_id}")

    return JsonResponse({"ok": True})


def om_mock_checkout(request):
    """
    Page locale simulant le checkout Orange Money en sandbox.
    Permet de simuler un paiement réussi ou échoué sans appeler Orange.
    """
    tx = request.GET.get("transaction_id") or ""
    if not tx:
        return HttpResponse("transaction_id manquant", status=400)
    
    return render(request, "store/om_mock_checkout.html", {"transaction_id": tx})


@require_http_methods(["POST"])
def om_mock_confirm(request):
    """
    Vue interne pour simuler un paiement réussi ou échoué en mode mock.
    Met à jour le Payment/Order puis redirige vers om_return.
    """
    tx = request.POST.get("transaction_id") or ""
    action = request.POST.get("action", "success")  # "success" ou "failed"
    
    if not tx:
        return HttpResponse("transaction_id manquant", status=400)
    
    # Retrouver l'Order
    order = Order.objects.filter(provider_ref=tx).first()
    
    if not order:
        logger.warning(f"[OM][mock_confirm] Order introuvable pour transaction_id={tx}")
        messages.error(request, "Transaction introuvable.")
        return redirect("store:om_return")
    
    if action == "success":
        try:
            order.mark_paid(provider="orange", provider_tx=tx)
            logger.info(f"[OM][mock_confirm] Paiement simulé réussi pour {tx}")
            
            messages.success(request, "Paiement simulé avec succès ✅")
            
            # Rediriger selon le type de commande
            if _is_kit_complete_order(order):
                # Pour le Kit complet : créer KitOrder et rediriger vers la page de succès
                try:
                    from store.services.kit_orders import (
                        create_kit_order_from_payment,
                        send_kit_order_confirmation_email,
                    )
                    kit_order = create_kit_order_from_payment(order)
                    send_kit_order_confirmation_email(kit_order)
                    logger.info(
                        f"[OM][mock_confirm] KitOrder créé: {kit_order.tracking_id}"
                    )
                    return redirect(
                        "store:kit_payment_success",
                        tracking_id=kit_order.tracking_id,
                    )
                except Exception:
                    logger.exception(
                        "[OM][mock_confirm] Erreur création KitOrder, fallback"
                    )
                    # Fallback vers l'ancienne page
                    from store.models import ClientInquiry
                    inquiry = ClientInquiry.objects.filter(
                        order=order, kind=ClientInquiry.KIND_KIT
                    ).first()
                    if inquiry and inquiry.selected_tier_code:
                        return redirect(
                            f"{reverse('store:kit_inquiry_success')}?tier={inquiry.selected_tier_code}&paid=1"
                        )
                    return redirect(f"{reverse('store:kit_inquiry_success')}?paid=1")
            else:
                # Pour l'ebook standard : envoyer email de fulfillment et rediriger
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
                    logger.info(
                        f"[OM][mock_confirm] Email fulfillment envoyé pour ebook"
                    )
                except Exception:
                    logger.exception("[OM][mock_confirm] Erreur envoi email de fulfilment")
                
                # Rediriger vers la page de téléchargement
                try:
                    return redirect("downloads:secure", order_uuid=order.uuid)
                except Exception:
                    return redirect("store:om_return", order_id=tx)
        except Exception:
            logger.exception(f"[OM][mock_confirm] Erreur mark_paid pour {tx}")
            messages.error(request, "Erreur lors de la simulation du paiement.")
    else:
        # Paiement échoué
        try:
            order.status = Order.FAILED
            order.save(update_fields=["status"])
            logger.info(f"[OM][mock_confirm] Paiement simulé échoué pour {tx}")
            messages.error(request, "Paiement simulé échoué.")
        except Exception:
            logger.exception(f"[OM][mock_confirm] Erreur mark_failed pour {tx}")
    
    return redirect("store:om_return", order_id=tx)


@require_http_methods(["POST"])
def kit_pay_om_start(request, inquiry_id):
    """
    Démarre un paiement Orange Money pour le Kit complet.
    """
    inquiry = get_object_or_404(ClientInquiry, pk=inquiry_id, kind=ClientInquiry.KIND_KIT)
    
    # Déterminer le montant du Kit complet pour cette inquiry
    amount = inquiry.estimated_price_fcfa
    if not amount:
        # Fallback : calculer depuis les tiers
        from store.views import _get_kit_tiers, _estimate_kit_price, _compute_org_factor_from_inquiry
        tiers = _get_kit_tiers()
        tier = next((t for t in tiers if t["code"] == inquiry.selected_tier_code), None)
        if not tier:
            tier = tiers[1] if len(tiers) > 1 else tiers[0]
        org_factor = _compute_org_factor_from_inquiry(inquiry)
        estimate = _estimate_kit_price(
            tier_code=tier["code"],
            docs_count=inquiry.docs_count or 1,
            complexity=getattr(inquiry, "complexity", "standard"),
            org_factor=org_factor,
        )
        amount = estimate["suggested_price"]
    
    if not amount or amount <= 0:
        messages.error(request, "Montant invalide pour cette commande.")
        return redirect("store:kit_quote", pk=inquiry.id)
    
    # Récupérer ou créer l'Order
    product = Product.objects.filter(slug="audit-sans-peur").first()
    if not product:
        messages.error(request, "Produit introuvable.")
        return redirect("store:kit_quote", pk=inquiry.id)
    
    # Si l'inquiry a déjà un order, on l'utilise, sinon on en crée un
    order = getattr(inquiry, "order", None)
    if not order:
        from store.models import OfferTier
        import uuid
        kit_tier = OfferTier.objects.filter(product=product, kind="KIT").first() \
                   or OfferTier.objects.filter(product=product, kind="STANDARD").first()
        order = Order.objects.create(
            product=product,
            tier_id=kit_tier.id if kit_tier else None,
            email=inquiry.email,
            first_name=inquiry.contact_name or "",
            last_name="",
            phone=getattr(inquiry, "phone", ""),
            amount_fcfa=amount,
            currency="XOF",
            status="CREATED",
            provider_ref=f"KIT-{uuid.uuid4().hex}",
        )
        inquiry.order = order
        inquiry.save(update_fields=["order"])
    
    try:
        payment_url, order_id = orange_money.create_checkout(
            inquiry_id=inquiry.id,
            amount=amount,
            currency="XOF",
            request=request,
        )
        
        # Mettre à jour order.provider_ref avec l'order_id retourné
        order.provider_ref = order_id
        order.save(update_fields=["provider_ref"])
        
        return redirect(payment_url)
        
    except orange_money.OrangeMoneyAuthError as e:
        logger.error(f"[OM][kit_pay_om_start] Erreur OAuth: {e}")
        messages.error(
            request,
            "Erreur d'authentification Orange Money. Veuillez réessayer plus tard."
        )
        return redirect("store:kit_quote", pk=inquiry.id)
    except orange_money.OrangeMoneyAPIError as e:
        # Log détaillé de l'erreur API avec status_code et response_data
        logger.error(
            f"[OM][kit_pay_om_start] Erreur API (status={getattr(e, 'status_code', 'N/A')}): {e}"
        )
        if hasattr(e, 'response_data') and e.response_data:
            logger.error(
                f"[OM][kit_pay_om_start] Response data: {json.dumps(e.response_data, ensure_ascii=False)}"
            )
        
        # Message utilisateur convivial selon le code d'erreur
        status_code = getattr(e, 'status_code', None)
        if status_code and status_code != 201:
            messages.error(
                request,
                f"Le service de paiement Orange Money a retourné une erreur (code {status_code}). "
                f"Veuillez réessayer ou utiliser un autre moyen de paiement."
            )
        else:
            messages.error(
                request,
                "Le paiement Orange Money n'est pas disponible pour le moment. "
                "Veuillez réessayer plus tard ou utiliser un autre moyen de paiement."
            )
        return redirect("store:kit_quote", pk=inquiry.id)
    except orange_money.OrangeMoneyError as e:
        logger.error(f"[OM][kit_pay_om_start] Erreur OM: {e}")
        messages.error(
            request,
            "Le paiement Orange Money n'est pas disponible pour le moment. "
            "Veuillez réessayer plus tard ou utiliser un autre moyen de paiement."
        )
        return redirect("store:kit_quote", pk=inquiry.id)
    except Exception as e:
        logger.exception(f"[OM][kit_pay_om_start] Erreur inattendue: {e}")
        messages.error(request, "Une erreur est survenue lors de l'initialisation du paiement.")
        return redirect("store:kit_quote", pk=inquiry.id)


def cinetpay_mock_checkout(request):
    """
    Page locale simulant le checkout CinetPay en sandbox.
    Permet de cliquer pour confirmer le paiement (redirige vers cinetpay_return).
    """
    tx = request.GET.get("transaction_id") or ""
    if not tx:
        return HttpResponse("transaction_id manquant", status=400)
# <<<<<<< HEAD
    logger.warning(f"[CINETPAY MOCK] ⚠️ MODE MOCK ACTIVÉ - checkout page for tx={tx}")
    logger.warning(f"[CINETPAY MOCK] ⚠️ Redirection automatique vers cinetpay_return (simulation)")
    # Redirection immédiate vers la vue de retour
    # (peut être remplacée par une page avec bouton)
    from django.urls import reverse
    return redirect(f"{reverse('store:cinetpay_return')}?transaction_id={tx}")
# =======
    logger.info(f"[CINETPAY MOCK] checkout page for tx={tx}")
    return render(request, "store/cinetpay_mock_checkout.html", {"tx": tx})


# === NOUVELLES VUES ORANGE MONEY POUR EBOOK ===

def orange_checkout(request, product_slug):
    """
    Vue de checkout Orange Money pour l'ebook "Audit Sans Peur".
    """
    product = get_object_or_404(Product, slug=product_slug, is_published=True)
    provider = "orange_money_ml"

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            # 1) Créer l'objet Order (status = PENDING, provider via provider_ref)
            order = Order.objects.create(
                product=product,
                amount_fcfa=product.price_fcfa,
                currency="XOF",
                status="PENDING",
                email=form.cleaned_data["email"],
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
                phone=form.cleaned_data.get("phone", ""),
            )

            # 2) Appeler le service Orange Money (sandbox)
            try:
                customer_msisdn = form.cleaned_data.get("phone") or ""
                if not customer_msisdn:
                    # Utiliser le numéro test sandbox par défaut
                    from django.conf import settings
                    config = getattr(settings, 'ORANGE_MONEY', None)
                    customer_msisdn = config.test_subscriber_msisdn if config else "77011011234"

                om_response = orange_money.create_sandbox_payment_request(
                    order=order,
                    customer_msisdn=customer_msisdn,
                )

                # 3) Stocker la référence provider
                provider_reference = om_response.get("provider_reference")
                if provider_reference:
                    order.provider_ref = provider_reference
                    order.save(update_fields=["provider_ref"])

                # 4) Redirection vers la page de mock checkout
                return redirect("store:orange_mock_checkout", provider_ref=provider_reference)

            except orange_money.OrangeMoneyError as e:
                logger.error(f"[ORANGE_CHECKOUT] Erreur OM: {e}")
                messages.error(request, f"Erreur Orange Money: {e}")
                return render(request, "store/checkout.html", {
                    "form": form,
                    "product": product,
                    "provider": provider,
                    "tier": None,
                })
            except Exception as e:
                logger.exception(f"[ORANGE_CHECKOUT] Erreur inattendue: {e}")
                messages.error(request, "Une erreur est survenue lors de l'initialisation du paiement.")
                return render(request, "store/checkout.html", {
                    "form": form,
                    "product": product,
                    "provider": provider,
                    "tier": None,
                })
    else:
        form = PaymentForm()

    return render(
        request,
        "store/checkout.html",
        {
            "form": form,
            "product": product,
            "provider": provider,
            "tier": None,
        },
    )


def orange_mock_checkout(request, provider_ref):
    """
    Page de mock checkout Orange Money pour simuler l'interface de paiement.
    """
    order = get_object_or_404(Order, provider_ref=provider_ref)
    
    return render(
        request,
        "store/om_mock_checkout.html",
        {
            "payment": order,
            "order": order,
            "product": order.product,
        },
    )


@require_http_methods(["GET", "POST"])
def orange_mock_success(request, provider_ref):
    """
    Simule un paiement Orange Money réussi.
    """
    order = get_object_or_404(Order, provider_ref=provider_ref)
    
    if order.status != "PAID":
        # Marquer comme payé et déclencher la finalisation
        order.mark_paid(provider="orange_money_ml", provider_tx=order.provider_ref)
        
        # Finaliser le paiement (créer tokens, envoyer email)
        success = payments.finalize_successful_payment(order)
        if success:
            messages.success(request, "Paiement simulé avec succès ! Vérifiez votre email pour les liens de téléchargement.")
        else:
            messages.warning(request, "Paiement enregistré mais erreur lors de l'envoi de l'email. Contactez le support.")

    return render(request, "store/payment_success.html", {"payment": order, "order": order})


@require_http_methods(["GET", "POST"])
def orange_mock_failure(request, provider_ref):
    """
    Simule un paiement Orange Money échoué.
    """
    order = get_object_or_404(Order, provider_ref=provider_ref)
    
    if order.status != "FAILED":
        order.status = "FAILED"
        order.save(update_fields=["status"])

    messages.error(request, "Paiement simulé échoué. Veuillez réessayer.")
    return render(request, "store/payment_failure.html", {"payment": order, "order": order})


def orange_start_payment(request, product_slug):
    """
    Démarre un paiement Orange Money WebPay Dev.
    Crée un Payment (status="PENDING"), appelle l'API Orange Money,
    et redirige l'utilisateur vers le payment_url.
    
    Conforme au guide officiel Orange Money WebPay Dev.
    """
    product = get_object_or_404(Product, slug=product_slug, is_published=True)
    
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            
            # Créer l'Order
            order = Order.objects.create(
                product=product,
                amount_fcfa=product.price_fcfa,
                currency="XOF",
                status="PENDING",
                email=cd["email"],
                first_name=cd.get("first_name", ""),
                last_name=cd.get("last_name", ""),
                phone=cd.get("phone", ""),
            )
            
            try:
                # Appeler l'API Orange Money pour créer le paiement
                result = orange_money.create_payment_request(order)
                payment_url = result["payment_url"]
                pay_token = result.get("pay_token")
                order_id = result["order_id"]
                
                # Enregistrer la référence provider
                order.provider_ref = order_id
                if pay_token:
                    # Stocker le pay_token dans cinetpay_payment_id (legacy field)
                    order.cinetpay_payment_id = pay_token
                order.save(update_fields=["provider_ref", "cinetpay_payment_id"])
                
                # Stocker la réponse brute dans un Payment si le modèle existe
                try:
                    payment = Payment.objects.create(
                        order_id=order_id,
                        provider_tx_id=pay_token or order_id,
                        status="PENDING",
                        amount=int(order.amount_fcfa),
                        currency="XOF",
                        email=order.email,
                    )
                    # Stocker la réponse brute si possible
                    if hasattr(payment, 'raw_response'):
                        payment.raw_response = result.get("raw_response", {})
                        payment.save(update_fields=["raw_response"])
                except Exception as e:
                    logger.warning(f"[OM][start] Erreur création Payment: {e}")
                
                # Rediriger vers l'URL de paiement Orange Money
                logger.info(f"[OM][start] Redirection vers Orange Money: {payment_url}")
                return redirect(payment_url)
                
            except orange_money.OrangeMoneyAuthError as e:
                logger.error(f"[OM][start] Erreur OAuth: {e}")
                messages.error(
                    request,
                    "Erreur d'authentification Orange Money. Veuillez réessayer plus tard."
                )
                # Supprimer l'ordre créé si l'authentification échoue
                order.delete()
            except orange_money.OrangeMoneyAPIError as e:
                # Log détaillé de l'erreur API avec status_code et response_data
                logger.error(
                    f"[OM][start] Erreur API (status={getattr(e, 'status_code', 'N/A')}): {e}"
                )
                if hasattr(e, 'response_data') and e.response_data:
                    logger.error(
                        f"[OM][start] Response data: {json.dumps(e.response_data, ensure_ascii=False)}"
                    )
                
                # Message utilisateur convivial selon le code d'erreur
                status_code = getattr(e, 'status_code', None)
                if status_code and status_code != 201:
                    messages.error(
                        request,
                        f"Le service de paiement Orange Money a retourné une erreur (code {status_code}). "
                        f"Veuillez vérifier vos informations et réessayer."
                    )
                else:
                    messages.error(
                        request,
                        "Erreur lors de l'initialisation du paiement Orange Money. "
                        "Veuillez réessayer ou contacter le support."
                    )
                # Supprimer l'ordre créé si l'API échoue
                order.delete()
            except Exception as e:
                logger.exception(f"[OM][start] Erreur inattendue: {e}")
                messages.error(
                    request,
                    "Une erreur est survenue. Veuillez réessayer ou contacter le support."
                )
                # Supprimer l'ordre créé en cas d'erreur inattendue
                order.delete()
        else:
            messages.error(request, "Formulaire invalide.")
    else:
        form = PaymentForm()
    
    return render(
        request,
        "store/checkout.html",
        {
            "form": form,
            "product": product,
            "provider": "orange_money_ml",
            "tier": None,
        },
    )


@require_http_methods(["GET"])
def orange_return(request):
    """
    Page de retour après paiement Orange Money (return_url).
    
    IMPORTANT: Ne pas valider le paiement ici. Le webhook (notify_url) est la seule source de vérité.
    Affiche une page de succès professionnelle avec liens de téléchargement si payé,
    sinon une page "en cours de validation".
    """
    from store.utils.downloads import build_download_urls_for_order
    
    order_id = request.GET.get("order_id") or request.GET.get("orderId")
    
    if not order_id:
        return render(
            request,
            "store/payments/orange_unknown.html",
            {"error": "Référence de commande manquante"},
        )
    
    # Retrouver l'Order
    order = Order.objects.filter(provider_ref=order_id).first()
    if not order:
        # Essayer avec uuid
        try:
            import uuid as uuid_module
            order = Order.objects.filter(
                uuid=uuid_module.UUID(order_id)
            ).first()
        except (ValueError, TypeError):
            pass
    
    if not order:
        logger.warning(f"[OM][return] Order introuvable pour order_id={order_id}")
        return render(
            request,
            "store/payments/orange_unknown.html",
            {"error": "Commande introuvable", "order_id": order_id},
        )
    
    # Vérifier si le paiement est déjà validé (via webhook)
    if order.status == "PAID":
        # Le webhook a déjà traité le paiement
        # Stocker les infos en session pour accès sécurisé
        request.session["order_email"] = order.email
        paid_orders = set(request.session.get("paid_orders", []))
        paid_orders.add(str(order.uuid))
        request.session["paid_orders"] = list(paid_orders)
        request.session.modified = True
        
        # Construire les URLs de téléchargement
        download_urls = build_download_urls_for_order(order)
        
        # Afficher la page de succès avec tous les liens
        return render(
            request,
            "store/payments/orange_success.html",
            {
                "order": order,
                "product": order.product,
                "payment_ref": order.provider_ref,
                "amount": order.amount_fcfa,
                **download_urls,
            },
        )
    
    # Sinon, afficher la page "en cours de validation"
    return render(
        request,
        "store/payments/orange_pending.html",
        {
            "order": order,
            "order_id": order_id,
            "product": order.product,
            "message": "Votre paiement est en cours de validation. Vous recevrez une confirmation par email sous peu.",
        },
    )


def orange_cancel(request):
    """
    Page d'annulation de paiement Orange Money (cancel_url).
    
    Affiche un message informatif et propose de réessayer le paiement.
    """
    order_id = request.GET.get("order_id") or request.GET.get("orderId")
    
    order = None
    product = None
    retry_url = None
    
    if order_id:
        # Retrouver l'Order
        order = Order.objects.filter(provider_ref=order_id).first()
        if not order:
            # Essayer avec uuid
            try:
                import uuid as uuid_module
                order = Order.objects.filter(
                    uuid=uuid_module.UUID(order_id)
                ).first()
            except (ValueError, TypeError):
                pass
        
        if order:
            product = order.product
            # Construire l'URL de retry vers la page de checkout
            if product:
                retry_url = reverse("store:buy", kwargs={"slug": product.slug}) + "?provider=orange_money_ml"
    
    # Si pas de produit identifié, lien vers la page d'offres
    if not retry_url:
        retry_url = reverse("store:offers")
    
    return render(
        request,
        "store/payments/orange_cancel.html",
        {
            "order": order,
            "product": product,
            "order_id": order_id,
            "retry_url": retry_url,
        },
    )


@csrf_exempt
@require_http_methods(["POST", "GET"])
def orange_notify(request):
    """
    Webhook Orange Money (notify_url).
    
    Reçoit la notification Orange Money et valide le paiement.
    C'est la SEULE source de vérité pour valider un paiement.
    
    Conforme au guide officiel Orange Money WebPay Dev.
    """
    if request.method == "GET":
        # Health check
        return HttpResponse("OK", status=200)
    
    try:
        # Vérifier et parser le webhook
        payload = orange_money.verify_webhook(request)
        if not payload:
            logger.warning("[OM][notify] Webhook invalide ou payload vide")
            return HttpResponse("Invalid webhook", status=400)
        
        logger.info(f"[OM][notify] Payload reçu: {json.dumps(payload, indent=2)}")
        
        # Extraire les informations selon le format Orange Money (guide)
        # Format attendu selon guide (section 3.3):
        # {
        #   "status": "SUCCESS",
        #   "notif_token": "dd497bda3b250e536186fc0663f32f40",
        #   "txnid": "MP150709.1341.A00073"
        # }
        # Note: order_id n'est pas dans le webhook selon le guide,
        # mais on peut le récupérer via txnid ou le chercher autrement
        status = payload.get("status", "").upper()
        notif_token = payload.get("notif_token")
        txnid = payload.get("txnid")
        
        # Selon le guide, le webhook contient: status, notif_token, txnid
        # Pas d'order_id dans le webhook, donc on doit retrouver l'Order autrement
        # Options:
        # 1. Chercher par pay_token (stocké dans cinetpay_payment_id)
        # 2. Chercher par txnid (si stocké)
        # 3. Utiliser order_id depuis GET params (si Orange l'envoie)
        order_id = (
            payload.get("order_id")
            or payload.get("orderId")
            or request.GET.get("order_id")
        )
        txnid = payload.get("txnid")
        pay_token = payload.get("pay_token")
        
        # Retrouver l'Order
        order = None
        if order_id:
            # Si order_id est présent (via GET params ou payload)
            order = Order.objects.filter(provider_ref=order_id).first()
            if not order:
                try:
                    import uuid as uuid_module
                    order = Order.objects.filter(
                        uuid=uuid_module.UUID(order_id)
                    ).first()
                except (ValueError, TypeError):
                    pass
        
        # Fallback: chercher par pay_token (stocké dans cinetpay_payment_id)
        if not order and pay_token:
            order = Order.objects.filter(cinetpay_payment_id=pay_token).first()
        
        # Fallback: chercher par txnid si stocké quelque part
        # (pour l'instant, on ne stocke pas txnid, mais on peut l'ajouter)
        
        if not order:
            logger.warning(
                f"[OM][notify] Order introuvable: order_id={order_id}, "
                f"txnid={txnid}, pay_token={pay_token}"
            )
            return HttpResponse("Order not found", status=404)
        
        # Vérifier si déjà payé (idempotence)
        if order.status == "PAID":
            logger.info(
                f"[OM][notify] Order {order.id} déjà payé, ignoré"
            )
            return JsonResponse({"status": "ok", "message": "Already processed"})
        
        # Vérifier le notif_token si disponible (sécurité selon guide)
        # Le notif_token est retourné dans la réponse de create_payment_request
        # et doit correspondre à celui reçu dans le webhook
        if notif_token:
            # Récupérer le notif_token stocké (depuis Payment.raw_response)
            stored_notif_token = None
            try:
                payment = Payment.objects.filter(order_id=order.provider_ref).first()
                if payment and hasattr(payment, 'raw_response'):
                    stored_notif_token = payment.raw_response.get("notif_token")
            except Exception:
                pass
            
            if stored_notif_token and stored_notif_token != notif_token:
                logger.warning(
                    f"[OM][notify] notif_token mismatch: "
                    f"attendu={stored_notif_token}, reçu={notif_token}"
                )
                # Pour l'instant, on log juste (en prod, on pourrait rejeter)
            else:
                logger.info(
                    f"[OM][notify] notif_token vérifié: {notif_token}"
                )
        
        # Mapper le statut Orange Money
        if orange_money.map_provider_status_to_paid(status):
            # Paiement réussi
            logger.info(f"[OM][notify] Paiement confirmé pour order_id={order_id}, status={status}")
            
            # Marquer la commande comme payée
            order.mark_paid(
                provider="orange_money_ml",
                provider_tx=txnid or pay_token or order.provider_ref,
                trigger_fulfillment=True,
            )
            
            # Finaliser le paiement (créer tokens, envoyer email)
            try:
                success = payments.finalize_successful_payment(order)
                if success:
                    logger.info(f"[OM][notify] Finalisation réussie pour order {order.id}")
                else:
                    logger.error(f"[OM][notify] Erreur finalisation pour order {order.id}")
            except Exception as e:
                logger.exception(f"[OM][notify] Erreur finalisation: {e}")
            
            # Mettre à jour le Payment si existe
            try:
                payment = Payment.objects.filter(order_id=order_id).first()
                if payment:
                    payment.status = "PAID"
                    payment.provider_tx_id = pay_token or order_id
                    if hasattr(payment, 'raw_response'):
                        payment.raw_response = payload
                    payment.save()
            except Exception as e:
                logger.warning(f"[OM][notify] Erreur mise à jour Payment: {e}")
        else:
            # Paiement échoué
            logger.info(f"[OM][notify] Paiement échoué pour order_id={order_id}, status={status}")
            order.status = "FAILED"
            order.save(update_fields=["status"])
            
            # Mettre à jour le Payment si existe
            try:
                payment = Payment.objects.filter(order_id=order_id).first()
                if payment:
                    payment.status = "FAILED"
                    if hasattr(payment, 'raw_response'):
                        payment.raw_response = payload
                    payment.save()
            except Exception as e:
                logger.warning(f"[OM][notify] Erreur mise à jour Payment: {e}")
        
        # Retourner OK à Orange Money
        return JsonResponse({"status": "ok"})
    
    except Exception as e:
        logger.exception(f"[OM][notify] Erreur traitement webhook: {e}")
        return HttpResponse("Internal error", status=500)


def orange_api_test(request):
    """
    Vue de test pour vérifier la connexion à l'API Orange Money.
    Accessible uniquement en mode DEBUG.
    """
    from django.conf import settings
    
    if not settings.DEBUG:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Cette page n'est disponible qu'en mode DEBUG")
    
    from store.services import orange_money
    import json
    
    context = {
        'config_loaded': False,
        'config': None,
        'test_result': None,
        'error': None,
    }
    
    # Vérifier la configuration
    try:
        config = orange_money.get_orange_config()
        if config:
            context['config_loaded'] = True
            context['config'] = {
                'env': config.env,
                'base_url': config.base_url,
                'merchant_msisdn': config.merchant_msisdn or "❌ Non défini",
                'merchant_code': config.merchant_code or "❌ Non défini",
                'login': config.login or "❌ Non défini",
                'password': "***" if config.password else "❌ Non défini",
                'test_subscriber_msisdn': config.test_subscriber_msisdn,
                'currency': config.currency,
                'country': config.country,
            }
    except Exception as e:
        context['error'] = f"Erreur de configuration: {e}"
    
    # Tester l'API si demandé
    if request.method == 'POST' and 'test_api' in request.POST:
        try:
            from store.models import Product, Order
            # Créer un Order de test
            product = Product.objects.filter(is_published=True).first()
            if not product:
                context['error'] = "Aucun produit publié trouvé pour le test"
            else:
                test_order = Order(
                    product=product,
                    amount_fcfa=100,  # 1 FCFA pour le test
                    currency="XOF",
                    status="PENDING",
                    email="test@example.com",
                    first_name="Test",
                    last_name="User",
                    phone="77011011234",
                )
                test_order.save()
                
                # Tester l'appel API
                result = orange_money.create_sandbox_payment_request(
                    order=test_order,
                    customer_msisdn="77011011234",
                )
                
                # Formater la réponse API pour l'affichage
                api_response = result.get('api_response')
                if api_response:
                    try:
                        import json
                        api_response_formatted = json.dumps(api_response, indent=2, ensure_ascii=False)
                    except:
                        api_response_formatted = str(api_response)
                else:
                    api_response_formatted = None
                
                context['test_result'] = {
                    'success': True,
                    'provider_reference': result.get('provider_reference'),
                    'status': result.get('status'),
                    'api_response': api_response_formatted,
                }
                
                # Nettoyer l'Order de test
                test_order.delete()
        except orange_money.OrangeMoneyError as e:
            context['test_result'] = {
                'success': False,
                'error': str(e),
            }
        except Exception as e:
            context['test_result'] = {
                'success': False,
                'error': f"Erreur inattendue: {e}",
            }
            import traceback
            context['test_result']['traceback'] = traceback.format_exc()
    
    return render(request, "store/orange_api_test.html", context)


@csrf_exempt
def orange_callback(request):
    """
    Endpoint de callback Orange Money pour les notifications de paiement.
    """
    if request.method == "GET":
        return HttpResponse("OK", status=200)
    
    try:
        # Vérifier et parser le webhook
        payload = orange_money.verify_webhook(request)
        if not payload:
            logger.warning("[ORANGE_CALLBACK] Webhook invalide ou signature incorrecte")
            return HttpResponse("Invalid webhook", status=400)

        logger.info(f"[ORANGE_CALLBACK] Payload reçu: {payload}")

        # Extraire les informations du payload
        status = payload.get("status", "").upper()
        reference = payload.get("reference") or payload.get("transaction_id")
        
        if not reference:
            logger.warning("[ORANGE_CALLBACK] Référence manquante dans le payload")
            return HttpResponse("Missing reference", status=400)

        # Retrouver l'Order
        order = payments.get_payment_by_provider_reference(reference)
        if not order:
            logger.warning(f"[ORANGE_CALLBACK] Order introuvable pour référence={reference}")
            return HttpResponse("Order not found", status=404)

        # Traiter selon le statut
        if orange_money.map_provider_status_to_paid(status):
            # Paiement réussi
            if order.status != "PAID":
                order.mark_paid(provider="orange_money_ml", provider_tx=reference)
                
                # Finaliser le paiement
                success = payments.finalize_successful_payment(order)
                if success:
                    logger.info(f"[ORANGE_CALLBACK] Paiement finalisé avec succès pour {reference}")
                else:
                    logger.error(f"[ORANGE_CALLBACK] Erreur finalisation pour {reference}")
        else:
            # Paiement échoué
            if order.status not in ["FAILED", "PAID"]:
                order.status = "FAILED"
                order.save(update_fields=["status"])
                logger.info(f"[ORANGE_CALLBACK] Paiement marqué comme échoué pour {reference}")

        return JsonResponse({"status": "ok"})

    except Exception as e:
        logger.exception(f"[ORANGE_CALLBACK] Erreur traitement webhook: {e}")
        return HttpResponse("Internal error", status=500)
