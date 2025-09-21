import os

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from .models import DownloadableAsset, DownloadCategory, DownloadEntitlement, PurchaseClaim
from .services import check_site_purchase, user_has_access


class DownloadableAssetForm(forms.ModelForm):
    class Meta:
        model = DownloadableAsset
        fields = [
            "category", "title", "short_desc", "file", "slug", "is_published", "order"
        ]
        widgets = {
            "short_desc": forms.TextInput(
                attrs={"placeholder": "Une phrase courte…"}
            ),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if not slug:
            slug = slugify(
                self.cleaned_data.get("title") or ""
            )
        return slug


@login_required
@permission_required(
    "downloads.add_downloadableasset", raise_exception=True
)
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
    ext = (request.GET.get("ext") or "").upper().strip()
    assets_qs = category.assets.filter(is_published=True)
    if ext:
        assets_qs = [a for a in assets_qs if a.extension == ext]
    all_exts = sorted({a.extension for a in category.assets.filter(is_published=True)})
    ctx = {"category": category, "assets": assets_qs, "all_exts": all_exts, "active_ext": ext}
    # Option SEO soft : header pour robots
    response = render(request, "downloads/category_page.html", ctx) if not request.headers.get("HX-Request") \
        else render(request, "downloads/_asset_grid.html", ctx)
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
                ent, _ = DownloadEntitlement.objects.get_or_create(email=email, category=category, defaults={"source": "SITE"})
                request.session["verified_email"] = email
                messages.success(request, "Accès activé. Vous pouvez ouvrir la page maintenant.")
                return redirect(category.get_absolute_url())
            messages.error(request, "Achat introuvable pour cet email. Veuillez vérifier ou joindre une preuve.")
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
        messages.info(request, "Votre demande a été enregistrée. Vous recevrez un email dès validation.")
        return redirect("downloads_public:claim_access")
    cats = DownloadCategory.objects.filter(is_protected=True).order_by("order")
    return render(request, "downloads/claim_access.html", {"categories": cats})
