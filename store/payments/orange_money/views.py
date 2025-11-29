"""
Vues Django pour Orange Money Mali.
"""
import json
import logging
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST, require_GET

from store.models import Order, ClientInquiry
from .api import initiate_payment, OrangeMoneyAPIError, OrangeMoneyAuthError, OrangeMoneyConfigurationError
from .models import OrangeMoneyPayment, OrangeMoneyPaymentLog

logger = logging.getLogger(__name__)


def _build_absolute_url(request, url_name, **kwargs):
    """Construit une URL absolue depuis un nom de route Django."""
    from django.conf import settings
    base_url = getattr(settings, "SITE_URL", None)
    if not base_url:
        base_url = f"{request.scheme}://{request.get_host()}"
    return f"{base_url.rstrip('/')}{reverse(url_name, kwargs=kwargs)}"


@require_http_methods(["GET", "POST"])
def start_orange_payment(request, order_id=None, inquiry_id=None):
    """
    Démarre un paiement Orange Money.
    
    Supporte deux types d'objets :
    - Order (pour ebook) : order_id
    - ClientInquiry (pour Kit complet) : inquiry_id
    
    Args:
        request: Request Django
        order_id: ID de l'Order (optionnel)
        inquiry_id: ID du ClientInquiry (optionnel)
    """
    # Déterminer l'objet métier (Order ou ClientInquiry)
    order_obj = None
    inquiry_obj = None
    
    if order_id:
        order_obj = get_object_or_404(Order, pk=order_id)
    elif inquiry_id:
        inquiry_obj = get_object_or_404(ClientInquiry, pk=inquiry_id, kind=ClientInquiry.KIND_KIT)
        order_obj = inquiry_obj.order
        if not order_obj:
            messages.error(request, "Aucune commande associée à cette demande.")
            return redirect("store:kit_quote", pk=inquiry_id)
    else:
        messages.error(request, "Paramètres manquants.")
        return redirect("/")
    
    if not order_obj:
        messages.error(request, "Commande introuvable.")
        return redirect("/")
    
    # Vérifier que la commande n'est pas déjà payée
    if order_obj.status == "PAID":
        messages.info(request, "Cette commande est déjà payée.")
        if inquiry_obj:
            return redirect("store:kit_payment_success", tracking_id=inquiry_obj.kit_orders.first().tracking_id if inquiry_obj.kit_orders.exists() else None)
        return redirect("downloads:secure", order_uuid=order_obj.uuid)
    
    # Récupérer le numéro MSISDN (depuis le formulaire ou l'Order)
    customer_msisdn = None
    if request.method == "POST":
        customer_msisdn = request.POST.get("customer_msisdn") or request.POST.get("phone")
    
    if not customer_msisdn:
        customer_msisdn = getattr(order_obj, "phone", None)
    
    # Fallback : utiliser le numéro test sandbox
    if not customer_msisdn:
        from django.conf import settings
        config = getattr(settings, "ORANGE_MONEY_CONFIG", {})
        customer_msisdn = config.get("MSISDN_TEST", "77011011234")
        logger.info(f"[OM][start] Utilisation du MSISDN test: {customer_msisdn}")
    
    # Normaliser le MSISDN (ajouter l'indicatif si nécessaire)
    if customer_msisdn and not customer_msisdn.startswith("223"):
        # Format Mali : 223 + numéro
        if len(customer_msisdn) == 9:
            customer_msisdn = f"223{customer_msisdn}"
    
    # Calculer le montant et la devise
    amount = int(order_obj.amount_fcfa)
    currency = order_obj.currency or "XOF"
    
    # Créer ou récupérer l'objet OrangeMoneyPayment
    om_payment, created = OrangeMoneyPayment.objects.get_or_create(
        reference=f"OM-{order_obj.provider_ref or order_obj.uuid}",
        defaults={
            "status": OrangeMoneyPayment.STATUS_INITIATED,
            "amount": amount,
            "currency": currency,
            "customer_msisdn": customer_msisdn,
            "merchant_id": "",
        }
    )
    
    # Lier l'objet métier
    if order_obj:
        om_payment.content_object = order_obj
        om_payment.save()
    
    # Construire les URLs de retour
    try:
        callback_url = _build_absolute_url(request, "store:orange_money:orange_notify")
        return_url_success = _build_absolute_url(request, "store:orange_money:orange_success")
        return_url_failed = _build_absolute_url(request, "store:orange_money:orange_failed")
    except Exception as e:
        logger.error(f"[OM][start] Erreur construction URLs: {e}")
        # Fallback : utiliser les URLs depuis settings
        from django.conf import settings
        config = getattr(settings, "ORANGE_MONEY_CONFIG", {})
        callback_url = config.get("CALLBACK_URL", "")
        return_url_success = config.get("RETURN_URL_SUCCESS", "")
        return_url_failed = config.get("RETURN_URL_FAILED", "")
    
    # Description du paiement
    description = f"{order_obj.product.title} - {order_obj.email}"
    if inquiry_obj:
        description = f"Kit Complet - {inquiry_obj.organization_name or inquiry_obj.contact_name}"
    
    # Initier le paiement via l'API Orange Money
    try:
        result = initiate_payment(
            amount=amount,
            currency=currency,
            customer_msisdn=customer_msisdn,
            external_reference=om_payment.reference,
            description=description,
            return_url_success=return_url_success,
            return_url_failed=return_url_failed,
            callback_url=callback_url,
        )
        
        # Mettre à jour l'objet OrangeMoneyPayment
        om_payment.external_transaction_id = result.get("transaction_id")
        om_payment.status = OrangeMoneyPayment.STATUS_PENDING
        om_payment.raw_request_payload = {
            "amount": amount,
            "currency": currency,
            "customer_msisdn": customer_msisdn,
            "reference": om_payment.reference,
        }
        om_payment.raw_response_payload = result.get("raw_response", {})
        om_payment.save()
        
        # Logger l'événement
        OrangeMoneyPaymentLog.objects.create(
            payment=om_payment,
            event_type=OrangeMoneyPaymentLog.EVENT_INIT,
            payload={"result": result},
        )
        
        # Gérer la redirection selon le type de flow
        payment_url = result.get("payment_url")
        
        if payment_url:
            # Flow avec URL de redirection
            logger.info(f"[OM][start] Redirection vers payment_url: {payment_url}")
            return redirect(payment_url)
        else:
            # Flow STK push (demande envoyée sur le téléphone)
            logger.info(f"[OM][start] Flow STK push pour {om_payment.reference}")
            return render(
                request,
                "payments/orange_money/pending.html",
                {
                    "payment": om_payment,
                    "order": order_obj,
                    "transaction_id": result.get("transaction_id"),
                }
            )
    
    except OrangeMoneyConfigurationError as e:
        logger.error(f"[OM][start] Erreur configuration: {e}")
        messages.error(
            request,
            "Orange Money n'est pas configuré. Veuillez contacter le support."
        )
        return redirect("store:buy", slug=order_obj.product.slug)
    
    except OrangeMoneyAuthError as e:
        logger.error(f"[OM][start] Erreur authentification: {e}")
        OrangeMoneyPaymentLog.objects.create(
            payment=om_payment,
            event_type=OrangeMoneyPaymentLog.EVENT_ERROR,
            payload={"error": str(e)},
        )
        messages.error(
            request,
            "Erreur d'authentification Orange Money. Veuillez réessayer plus tard."
        )
        return redirect("store:buy", slug=order_obj.product.slug)
    
    except OrangeMoneyAPIError as e:
        logger.error(f"[OM][start] Erreur API: {e}")
        OrangeMoneyPaymentLog.objects.create(
            payment=om_payment,
            event_type=OrangeMoneyPaymentLog.EVENT_ERROR,
            payload={"error": str(e), "status_code": e.status_code},
        )
        messages.error(
            request,
            f"Erreur lors de l'initiation du paiement: {e}"
        )
        return redirect("store:buy", slug=order_obj.product.slug)
    
    except Exception as e:
        logger.exception(f"[OM][start] Erreur inattendue: {e}")
        OrangeMoneyPaymentLog.objects.create(
            payment=om_payment,
            event_type=OrangeMoneyPaymentLog.EVENT_ERROR,
            payload={"error": str(e)},
        )
        messages.error(
            request,
            "Une erreur est survenue. Veuillez réessayer ou contacter le support."
        )
        return redirect("store:buy", slug=order_obj.product.slug)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def orange_payment_notify(request):
    """
    Callback/webhook Orange Money (notify_url).
    Appelé par Orange Money pour notifier le statut du paiement.
    """
    if request.method == "GET":
        # Health check
        return HttpResponse("OK", status=200)
    
    try:
        # Parser le payload JSON
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"[OM][notify] Erreur parsing JSON: {e}")
            return HttpResponseBadRequest("Invalid JSON")
        
        logger.info(f"[OM][notify] Payload reçu: {json.dumps(payload, indent=2)}")
        
        # Extraire les informations du payload
        # NOTE: La structure exacte dépend de la doc Orange Money Mali
        # Adapter selon la documentation officielle
        reference = payload.get("reference") or payload.get("order_id") or payload.get("transaction_id")
        status = payload.get("status", "").upper()
        transaction_id = payload.get("transaction_id") or payload.get("txnid")
        
        if not reference:
            logger.warning("[OM][notify] Référence manquante dans le payload")
            return HttpResponseBadRequest("Missing reference")
        
        # Retrouver le paiement Orange Money
        om_payment = OrangeMoneyPayment.objects.filter(reference=reference).first()
        if not om_payment:
            logger.warning(f"[OM][notify] Paiement introuvable pour référence={reference}")
            return HttpResponse("Payment not found", status=404)
        
        # Mettre à jour le paiement
        om_payment.callback_payload = payload
        if transaction_id:
            om_payment.external_transaction_id = transaction_id
        
        # Mapper le statut Orange Money vers notre statut
        if status in ["SUCCESS", "PAID", "COMPLETED", "ACCEPTED", "CONFIRMED"]:
            om_payment.status = OrangeMoneyPayment.STATUS_SUCCESS
        elif status in ["FAILED", "ERROR", "REJECTED"]:
            om_payment.status = OrangeMoneyPayment.STATUS_FAILED
        elif status in ["CANCELLED", "CANCELED"]:
            om_payment.status = OrangeMoneyPayment.STATUS_CANCELLED
        else:
            om_payment.status = OrangeMoneyPayment.STATUS_PENDING
        
        om_payment.save()
        
        # Logger l'événement
        OrangeMoneyPaymentLog.objects.create(
            payment=om_payment,
            event_type=OrangeMoneyPaymentLog.EVENT_CALLBACK,
            payload=payload,
        )
        
        # Si le paiement est réussi, marquer la commande comme payée
        if om_payment.status == OrangeMoneyPayment.STATUS_SUCCESS:
            order_obj = om_payment.content_object
            if order_obj and isinstance(order_obj, Order):
                if order_obj.status != "PAID":
                    try:
                        order_obj.mark_paid(
                            provider="orange_money",
                            provider_tx=transaction_id or reference,
                            trigger_fulfillment=True,
                        )
                        logger.info(
                            f"[OM][notify] Commande {order_obj.id} marquée comme payée"
                        )
                    except Exception as e:
                        logger.exception(
                            f"[OM][notify] Erreur mark_paid pour order {order_obj.id}: {e}"
                        )
        
        # Retourner une réponse OK à Orange Money
        return JsonResponse({"status": "ok", "message": "Callback processed"})
    
    except Exception as e:
        logger.exception(f"[OM][notify] Erreur traitement callback: {e}")
        return HttpResponse("Internal error", status=500)


@require_GET
def orange_payment_success(request):
    """
    Vue appelée lorsque l'utilisateur est redirigé après un paiement réussi.
    """
    reference = request.GET.get("reference") or request.GET.get("order_id") or request.GET.get("transaction_id")
    
    if not reference:
        return render(
            request,
            "payments/orange_money/success.html",
            {"error": "Référence manquante"},
        )
    
    # Retrouver le paiement
    om_payment = OrangeMoneyPayment.objects.filter(reference=reference).first()
    if not om_payment:
        logger.warning(f"[OM][success] Paiement introuvable pour référence={reference}")
        return render(
            request,
            "payments/orange_money/success.html",
            {"error": "Paiement introuvable"},
        )
    
    order_obj = om_payment.content_object
    
    # Vérifier si la commande est payée
    is_paid = False
    if order_obj and isinstance(order_obj, Order):
        is_paid = order_obj.status == "PAID"
    
    # Si le callback n'est pas encore arrivé, informer l'utilisateur
    if not is_paid and om_payment.status != OrangeMoneyPayment.STATUS_SUCCESS:
        return render(
            request,
            "payments/orange_money/pending.html",
            {
                "payment": om_payment,
                "order": order_obj,
                "message": "Votre paiement est en cours de traitement. Vous recevrez une confirmation par email sous peu.",
            }
        )
    
    # Rediriger selon le type de commande
    if order_obj and isinstance(order_obj, Order):
        # Vérifier si c'est un Kit complet
        inquiry = ClientInquiry.objects.filter(order=order_obj, kind=ClientInquiry.KIND_KIT).first()
        if inquiry:
            kit_order = inquiry.kit_orders.first()
            if kit_order:
                return redirect("store:kit_payment_success", tracking_id=kit_order.tracking_id)
            # Sinon, créer le KitOrder maintenant
            try:
                from store.services.kit_orders import create_kit_order_from_payment
                kit_order = create_kit_order_from_payment(order_obj)
                return redirect("store:kit_payment_success", tracking_id=kit_order.tracking_id)
            except Exception:
                logger.exception("[OM][success] Erreur création KitOrder")
        
        # Pour l'ebook, rediriger vers la page de téléchargement
        return redirect("downloads:secure", order_uuid=order_obj.uuid)
    
    # Fallback : afficher la page de succès générique
    return render(
        request,
        "payments/orange_money/success.html",
        {
            "payment": om_payment,
            "order": order_obj,
            "is_paid": is_paid,
        }
    )


@require_GET
def orange_payment_failed(request):
    """
    Vue appelée lorsque l'utilisateur est redirigé après un échec/annulation.
    """
    reference = request.GET.get("reference") or request.GET.get("order_id") or request.GET.get("transaction_id")
    
    if reference:
        om_payment = OrangeMoneyPayment.objects.filter(reference=reference).first()
        order_obj = om_payment.content_object if om_payment else None
    else:
        om_payment = None
        order_obj = None
    
    return render(
        request,
        "payments/orange_money/failed.html",
        {
            "payment": om_payment,
            "order": order_obj,
        }
    )

