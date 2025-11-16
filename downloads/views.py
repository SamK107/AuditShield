import os

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from store.models import DownloadToken, Order

from .models import (
    DownloadableAsset,
    DownloadCategory,
    DownloadEntitlement,
    PurchaseClaim,
)
from .services import SignedUrlService, check_site_purchase, user_has_access
from store.services.mailing import send_fulfilment_email
from .forms import ResendLinksForm


class DownloadableAssetForm(forms.ModelForm):
    class Meta:
        model = DownloadableAsset
        fields = ["category", "title", "short_desc", "file", "slug", "is_published", "order"]
        widgets = {
            "short_desc": forms.TextInput(attrs={"placeholder": "Une phrase courte…"}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if not slug:
            slug = slugify(self.cleaned_data.get("title") or "")
        return slug


@login_required
@permission_required("downloads.add_downloadableasset", raise_exception=True)
def asset_upload(request: HttpRequest) -> HttpResponse:
    """
    (Facultatif) Page interne pour déposer un fichier hors admin.
    Supprimer cette vue si non utilisée et ne garder que l'admin.
    """
    if request.method == "POST":
        form = DownloadableAssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save()
            return render(
                request,
                "downloads/asset_upload_success.html",
                {"asset": asset},
            )
    else:
        form = DownloadableAssetForm()
    return render(request, "downloads/asset_upload.html", {"form": form})


def asset_download(request: HttpRequest, slug: str) -> FileResponse:
    """
    Téléchargement direct par slug (/downloads/<slug>/).
    Conserver votre version si elle existe déjà.
    """
    asset = get_object_or_404(DownloadableAsset, slug=slug, is_published=True)
    file_handle = asset.file.open("rb")
    filename = os.path.basename(asset.file.name)
    return FileResponse(file_handle, as_attachment=True, filename=filename)


def category_page(request, slug):
    category = get_object_or_404(DownloadCategory, slug=slug)
    if not user_has_access(request, category):
        claim = reverse("downloads_public:claim_access")
        return redirect(f"{claim}?slug={category.slug}")
    # Utiliser les bons champs du modèle: is_published + order
    assets = (
        DownloadableAsset.objects
        .filter(category=category, is_published=True)
        .order_by("order", "id")
    )
    return render(request, "downloads/category_page.html", {"category": category, "assets": assets})

@require_http_methods(["GET","POST"])
def claim_access(request):
    slug = request.GET.get("slug") or request.POST.get("slug")
    category = get_object_or_404(DownloadCategory, slug=slug)
    # SKU requis pour cette catégorie
    sku = (category.required_sku or "").strip()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        if not email:
            messages.error(request, "Veuillez fournir votre adresse email.")
        else:
            # 1) Auto-validation d'un achat site
            if check_site_purchase(email=email, sku=sku):
                # On enregistre un entitlement email + SKU s'il n'existe pas
                DownloadEntitlement.objects.get_or_create(email=email, sku=sku, defaults={})
                # On enregistre aussi un entitlement par catégorie pour débloquer l’accès à la page
                DownloadEntitlement.objects.get_or_create(email=email, category=category, defaults={})
                # Create category entitlements for same SKU
                for s, val in PROTECTED_SLUGS.items():
                    if val == sku:
                        cat = DownloadCategory.objects.filter(slug=s).first()
                        if cat:
                            DownloadEntitlement.objects.get_or_create(email=email, category=cat, defaults={})
                request.session["download_claim_email"] = email
                messages.success(request, "Accès validé. Vous pouvez télécharger vos fichiers.")
                return redirect(category.page_path)
            else:
                # Sinon, dépôt de claim manuel (existant si déjà implémenté)
                messages.warning(request, "Achat non retrouvé automatiquement. Déposez une preuve d’achat pour validation manuelle.")
                # Redirect to manual claim form under the public namespace
                manual = reverse("downloads_public:manual_claim")
                return redirect(f"{manual}?slug={slug}&email={email}")

    return render(request, "downloads/claim_access.html", {"category": category, "sku": sku})


def secure_downloads(request: HttpRequest, order_uuid=None, token=None) -> HttpResponse:
    """
    Page sécurisée de téléchargement pour une commande payée.
    Accès par UUID (session) ou par token (partage).
    """
    if token:
        dt = DownloadToken.objects.filter(token=token).select_related("order").first()
        if not dt or not dt.is_valid():
            return HttpResponse("Lien de téléchargement invalide ou expiré.", status=410)
        order = dt.order
    elif order_uuid:
        order = get_object_or_404(Order, pk=order_uuid)
        if order.status != "PAID":
            return HttpResponse("Accès refusé : commande non payée.", status=403)
        if request.user.is_authenticated:
            if order.email.lower() != request.user.email.lower():
                return HttpResponse(
                    "Accès refusé : cette commande ne vous appartient pas.", status=403
                )
    else:
        return HttpResponse("Paramètre manquant.", status=400)

    # Extraction des 2 assets (A4, 6x9) pour le produit
    assets = DownloadableAsset.objects.filter(
        category__slug="ebook", is_published=True, title__iregex=r"A4|6.?x.?9"
    )

    asset_links = []
    for asset in assets:
        signed = SignedUrlService.get_signed_url(asset, expires=900)
        asset_links.append(
            {"title": asset.title, "extension": asset.extension, "signed_url": signed}
        )

    ctx = {"order": order, "asset_links": asset_links}
    return render(request, "downloads/secure_downloads.html", ctx)


def _get_two_assets_for_product(product):
    if product.download_slug:
        qs = DownloadableAsset.objects.filter(slug=product.download_slug, is_published=True)
    else:
        qs = DownloadableAsset.objects.filter(is_published=True)
    by_title_a4 = Q(title__iexact="PDF A4") | Q(title__icontains="A4")
    by_title_6x9 = Q(title__iregex=r"6.?x.?9") | Q(title__icontains="6x9")

    a4 = qs.filter(by_title_a4).first()
    x69 = qs.filter(by_title_6x9).first()
    return [a4, x69]


def download_secure_view(request, order_uuid):
    order = get_object_or_404(Order, uuid=order_uuid)
    if order.status != "PAID":
        return HttpResponseForbidden("Commande non payée.")

    session_email = request.session.get("order_email")
    paid_orders = set(request.session.get("paid_orders", []))
    valid_session = (
        session_email
        and session_email.lower() == order.email.lower()
        and str(order.uuid) in paid_orders
    )
    if not valid_session:
        return HttpResponseForbidden("Accès refusé.")

    assets = _get_two_assets_for_product(order.product)
    admin_msg = (
        ""
        if len(assets) == 2
        else (f"Publiez 'PDF A4' et 'PDF 6×9' (slug: {order.product.download_slug or '—'}).")
    )

    ctx = {"order": order, "assets": assets, "admin_message": admin_msg}
    return render(request, "downloads/secure.html", ctx)


def download_secure_with_token_view(request, order_uuid, token):
    order = get_object_or_404(Order, uuid=order_uuid)
    if order.status != "PAID":
        return HttpResponseForbidden("Commande non payée.")

    dt = get_object_or_404(DownloadToken, order=order, token=token)
    if not dt.is_valid():
        return HttpResponseForbidden("Lien expiré.")

    assets = _get_two_assets_for_product(order.product)
    admin_msg = "" if len(assets) == 2 else "Vérifiez l’admin: 'PDF A4' et 'PDF 6×9' manquants."
    ctx = {"order": order, "assets": assets, "admin_message": admin_msg}
    return render(request, "downloads/secure.html", ctx)


@require_http_methods(["POST"])
def resend_fulfilment_email(request, order_uuid):
    """
    Ré-envoie l'email de fulfilment (liens de téléchargement + bonus) à l'email de la commande.
    Accessible depuis la page sécurisée, avec les mêmes gardes d'accès.
    """
    order = get_object_or_404(Order, uuid=order_uuid)
    if order.status != "PAID":
        return HttpResponseForbidden("Commande non payée.")

    session_email = request.session.get("order_email")
    paid_orders = set(request.session.get("paid_orders", []))
    valid_session = (
        session_email
        and session_email.lower() == order.email.lower()
        and str(order.uuid) in paid_orders
    )
    if not valid_session:
        return HttpResponseForbidden("Accès refusé.")

    try:
        # Utilise l'UUID comme référence; le service retrouvera l'URL ressources et le lien bonus
        send_fulfilment_email(to_email=order.email, order_ref=str(order.uuid))
        messages.success(request, "Les liens de téléchargement ont été renvoyés à votre adresse email.")
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi de l'email: {e}")
    return redirect("downloads:secure", order_uuid=order.uuid)

@require_http_methods(["GET", "POST"])
def resend_links(request):
    """
    Formulaire public pour renvoyer les liens de téléchargement
    à partir d'une adresse email (dernière commande payée).
    """
    form = ResendLinksForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = (form.cleaned_data["email"] or "").strip()
        order = (
            Order.objects.filter(email__iexact=email, status="PAID")
            .order_by("-paid_at", "-created_at")
            .first()
        )
        if not order:
            messages.error(request, "Aucune commande payée trouvée pour cet email.")
        else:
            try:
                order_ref = order.provider_ref or order.cinetpay_payment_id or str(order.uuid)
                send_fulfilment_email(to_email=order.email, order_ref=order_ref)
                messages.success(request, "Un email avec vos liens de téléchargement vient d’être envoyé.")
                return redirect("downloads:resend_links")
            except Exception as e:
                messages.error(request, f"Erreur lors de l'envoi: {e}")
    return render(request, "downloads/resend_links_form.html", {"form": form})


def asset_serve_view(request, asset_id):
    asset = get_object_or_404(DownloadableAsset, pk=asset_id, is_published=True)
    filename = os.path.basename(asset.file.name)
    return FileResponse(asset.file.open("rb"), as_attachment=True, filename=filename)

def resources_overview(request, order_uuid):
    """
    Page unique listant toutes les ressources (hors ebook) groupées par catégorie,
    accessible après paiement via la session sécurisée (mêmes gardes que la page secure).
    """
    order = get_object_or_404(Order, uuid=order_uuid)
    if order.status != "PAID":
        return HttpResponseForbidden("Commande non payée.")
    session_email = request.session.get("order_email")
    paid_orders = set(request.session.get("paid_orders", []))
    valid_session = (
        session_email
        and session_email.lower() == order.email.lower()
        and str(order.uuid) in paid_orders
    )
    if not valid_session:
        return HttpResponseForbidden("Accès refusé.")
    # Récupère uniquement les catégories “ressources” (exclut ebooks)
    allowed_slugs = ("checklists", "outils-pratiques", "irregularites", "bonus")
    categories = (
        DownloadCategory.objects.filter(slug__in=allowed_slugs)
        .order_by("order", "slug")
    )
    data = []
    for cat in categories:
        if (cat.slug or "").lower() == "ebook":
            continue
        assets = (
            DownloadableAsset.objects.filter(category=cat, is_published=True).order_by(
                "order", "id"
            )
        )
        if not assets.exists():
            continue
        items = []
        for a in assets:
            try:
                signed = SignedUrlService.get_signed_url(a, expires=900)
            except Exception:
                signed = a.get_download_url()
            items.append(
                {
                    "id": a.id,
                    "title": a.title,
                    "short_desc": a.short_desc,
                    "extension": a.extension,
                    "url": signed,
                }
            )
        data.append(
            {
                "slug": cat.slug,
                "title": cat.title,
                "subtitle": cat.subtitle,
                "description": cat.description,
                "items": items,
            }
        )
    ctx = {"order": order, "groups": data}
    return render(request, "downloads/resources_overview.html", ctx)

from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMessage
from django.urls import reverse
from .forms import KitPreparationForm
from .models import ExternalEntitlement

def kit_preparation_start(request):
    if request.method == "POST":
        form = KitPreparationForm(request.POST, request.FILES)
        if form.is_valid():
            order_ref = form.cleaned_data["order_ref"].strip()
            email = form.cleaned_data["email"].strip().lower()
            submission_type = form.cleaned_data["submission_type"]

            # Debug: Afficher les valeurs dans les logs
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Recherche entitlement: order_ref={order_ref}, email={email}")

            # Vérifier si l'entitlement existe
            exists = ExternalEntitlement.objects.filter(
                order_ref__iexact=order_ref,
                email__iexact=email,
                category__slug="ebook",
            ).exists()

            # Debug: Afficher les entitlements trouvés
            all_matching = ExternalEntitlement.objects.filter(
                order_ref__iexact=order_ref,
                email__iexact=email,
            )
            logger.info(f"Entitlements trouvés: {list(all_matching.values('order_ref', 'email', 'category__slug'))}")

            if not exists:
                messages.error(request, f"Référence '{order_ref}' et/ou email '{email}' introuvable(s). Vérifiez vos informations.")
                logger.warning(f"Entitlement non trouvé: {order_ref} / {email}")
            else:
                to_email = getattr(settings, "CONTACT_INBOX_EMAIL", "contact@auditsanspeur.com")
                subject = f"[BONUS Kit Préparation] Texte client - {order_ref} - {email}"
                
                # Préparer l'email selon le type de soumission
                if submission_type == "file":
                    body = (
                        "Un client a soumis un fichier PDF pour le bonus Kit Préparation.\n\n"
                        f"Référence: {order_ref}\n"
                        f"Email: {email}\n"
                        "Voir la pièce jointe."
                    )
                    file = form.cleaned_data["file"]
                    msg = EmailMessage(subject=subject, body=body, to=[to_email])
                    msg.attach(file.name, file.read(), "application/pdf")
                else:
                    text_content = form.cleaned_data["text_content"]
                    body = (
                        "Un client a soumis un texte pour le bonus Kit Préparation.\n\n"
                        f"Référence: {order_ref}\n"
                        f"Email: {email}\n\n"
                        "=== TEXTE SOUMIS ===\n"
                        f"{text_content}"
                    )
                    msg = EmailMessage(subject=subject, body=body, to=[to_email])
                
                # Log détaillé avant envoi
                logger.info(f"📧 Préparation email pour {order_ref}")
                logger.info(f"   Destinataire: {to_email}")
                logger.info(f"   Sujet: {subject}")
                logger.info(f"   Type: {submission_type}")
                if submission_type == "file":
                    logger.info(f"   Fichier joint: {file.name} ({file.size} bytes)")
                else:
                    text_preview = text_content[:100] + "..." if len(text_content) > 100 else text_content
                    logger.info(f"   Texte (preview): {text_preview}")
                
                # Envoyer l'email avec gestion d'erreur
                try:
                    msg.send(fail_silently=False)
                    logger.info(f"✅ Email envoyé avec succès à {to_email} pour {order_ref}")
                    messages.success(request, "Merci ! Votre soumission a bien été transmise.")
                    return redirect(reverse("downloads_public:kit_preparation_thanks"))
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'envoi de l'email: {e}")
                    messages.error(request, f"Erreur lors de l'envoi: {str(e)}. Veuillez réessayer ou contacter le support.")
    else:
        form = KitPreparationForm()

    return render(request, "downloads/kit_preparation_start.html", {"form": form})

def kit_preparation_thanks(request):
    return render(request, "downloads/kit_preparation_thanks.html")
