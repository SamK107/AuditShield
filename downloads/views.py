import os

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

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


def category_page(request: HttpRequest, slug: str) -> HttpResponse:
    category = get_object_or_404(DownloadCategory, slug=slug)

    # 🔒 Gating d'accès
    if not user_has_access(request, category):
        messages.info(request, "Veuillez vérifier votre droit d’accès pour ouvrir cette page.")
        return redirect("downloads_public:claim_access")

    ext = (request.GET.get("ext") or "").strip()
    assets_qs = category.assets.filter(is_published=True)
    if ext:
        assets_qs = assets_qs.filter(extension=ext.upper())
        # ou, si casse variable :
        # assets_qs = assets_qs.filter(extension__iexact=ext)

    all_exts = sorted({a.extension for a in category.assets.filter(is_published=True)})

    ctx = {
        "category": category,
        "assets": assets_qs,
        "all_exts": all_exts,
        "active_ext": ext,
    }

    is_htmx = request.headers.get("HX-Request")
    tpl = "downloads/_asset_grid.html" if is_htmx else "downloads/category_page.html"
    response = render(request, tpl, ctx)

    if category.is_protected:
        response["X-Robots-Tag"] = "noindex, nofollow"

    return response


def claim_access(request: HttpRequest) -> HttpResponse:
    """
    Page permettant :
    - auto-validation si achat sur le SITE (email + SKU requis par la catégorie),
    - sinon dépôt d'une réclamation (plateforme externe) approuvée via l'admin.
    """
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        category_slug = request.POST.get("category")
        platform = request.POST.get("platform") or "SITE"
        order_ref = (request.POST.get("order_ref") or "").strip()
        category = get_object_or_404(DownloadCategory, slug=category_slug)
        if not email:
            messages.error(request, "Email requis.")
            return redirect("downloads_public:claim_access")
        # Cas SITE : auto-entitlement si commande trouvée
        if platform == "SITE":
            sku = category.required_sku or ""
            if not sku:
                messages.error(request, "Cette ressource nécessite un SKU défini côté admin.")
                return redirect("downloads_public:claim_access")
            if check_site_purchase(email, sku):
                ent, _ = DownloadEntitlement.objects.get_or_create(
                    email=email, category=category, defaults={"source": "SITE"}
                )
                request.session["verified_email"] = email
                messages.success(request, "Accès activé. Vous pouvez ouvrir la page maintenant.")
                return redirect(category.get_absolute_url())
            messages.error(
                request,
                "Achat introuvable pour cet email. Veuillez vérifier ou joindre une preuve.",
            )
        # Cas EXTERNAL : créer une réclamation à valider
        pc = PurchaseClaim(
            email=email,
            platform=platform,
            order_ref=order_ref,
            category=category,
        )
        if request.FILES.get("proof"):
            pc.proof = request.FILES["proof"]
        pc.save()
        messages.info(
            request, "Votre demande a été enregistrée. Vous recevrez un email dès validation."
        )
        return redirect("downloads_public:claim_access")
    cats = DownloadCategory.objects.filter(is_protected=True).order_by("order")
    return render(request, "downloads/claim_access.html", {"categories": cats})


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
