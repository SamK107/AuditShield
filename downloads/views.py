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


def asset_serve_view(request, asset_id):
    asset = get_object_or_404(DownloadableAsset, pk=asset_id, is_published=True)
    filename = os.path.basename(asset.file.name)
    return FileResponse(asset.file.open("rb"), as_attachment=True, filename=filename)
