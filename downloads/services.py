from django.utils import timezone
from downloads.models import ExternalEntitlement

try:
    from storages.backends.s3boto3 import S3Boto3Storage

    HAS_S3 = True
except Exception:
    HAS_S3 = False

from .models import DownloadableAsset, DownloadEntitlement, DownloadCategory


class SignedUrlService:
    @staticmethod
    def get_signed_url(asset: DownloadableAsset, *, expires=300) -> str:
        f = asset.file
        if not f:
            raise ValueError("File missing")
        if HAS_S3 and isinstance(f.storage, S3Boto3Storage):
            return f.storage.url(
                f.name,
                parameters={
                    "ResponseContentDisposition": f"attachment; filename={f.name.split('/')[-1]}"
                },
                expire=expires,
            )
        return f.url

    @staticmethod
    def update_analytics(asset: DownloadableAsset, request, kind="DOWNLOAD"):
        asset.download_count = (asset.download_count or 0) + 1
        asset.last_download_at = timezone.now()
        asset.save(update_fields=["download_count", "last_download_at"])
        # AssetEvent n'existe plus, donc on ne log plus d'événement détaillé ici.


ALWAYS_PROTECTED = {"bonus", "checklists", "outils-pratiques", "irregularites"}

def user_has_access(request, category: "DownloadCategory") -> bool:
    """
    Phase 1 gate for downloads:
    - If slug in ALWAYS_PROTECTED or category.is_protected: require entitlement
    - Else public
    """
    slug = (category.slug or "").strip().lower()
    # 1) Public if not protected and not in ALWAYS_PROTECTED
    if not category.is_protected and slug not in ALWAYS_PROTECTED:
        return True

    # 2) Protected: check entitlement on category
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        if DownloadEntitlement.objects.filter(user=user, category=category).exists():
            return True

    email = (request.session.get("download_claim_email") or "").strip()
    if email and DownloadEntitlement.objects.filter(email__iexact=email, category=category).exists():
        return True

    # 3) Deny
    return False


def check_site_purchase(email: str, sku: str) -> bool:
    """
    Vérifie si 'email' a une commande SITE payée contenant sku.
    S'adapte si le modèle Store diffère (retourne False plutôt que lever).
    """
    try:
        from store.models import Order  # Adapter si différent
    except Exception:
        return False
    try:
        q = Order.objects.filter(email=email).filter(status__in=["PAID", "SUCCEEDED", "COMPLETED"])
        if not q.exists():
            return False
        any_with_sku = q.filter(items__sku=sku).exists()
        if any_with_sku:
            return True
        return q.filter(sku=sku).exists()
    except Exception:
        return False
        
def user_has_access(request, category):
    # ... existant (tokens, commandes du site, etc.)

    # 1) Email de session (ex: après /claim)
    email = (getattr(request, "session", {}) or {}).get("claimed_email") or request.user.email if getattr(request, "user", None) and request.user.is_authenticated else None

    if email:
        # Achats externes importés (CSV)
        if ExternalEntitlement.objects.filter(email__iexact=email, category=category).exists():
            return True

    # 2) Code de claim (fallback si la plateforme ne donne pas l’email)
    code = request.session.get("claim_code")
    if code and ExternalEntitlement.objects.filter(claim_code=code, category=category).exists():
        return True

    # ... reste de ta logique existante ...
    return False
def _filesize_display(asset: DownloadableAsset) -> str | None:
    try:
        size = asset.file.size
    except Exception:
        return None
    units = ["B", "KB", "MB", "GB"]
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.1f} {units[i]}"


def attach_links_to_order(order):
    """
    Retourne une liste de liens de téléchargement pertinents pour la commande.
    Stratégie:
      - si Product.download_slug est renseigné → cet asset
      - sinon, on tente de trouver 2 variantes (A4, 6x9) publiées
    """
    links = []
    product = order.product
    assets = []

    if getattr(product, "download_slug", None):
        a = DownloadableAsset.objects.filter(slug=product.download_slug, is_published=True).first()
        if a:
            assets = [a]
    else:
        by_title_a4 = {"title__iexact": "PDF A4"}  # heuristique
        by_title_6x9 = {"title__icontains": "6x9"}
        a4 = DownloadableAsset.objects.filter(is_published=True, **by_title_a4).first()
        x69 = DownloadableAsset.objects.filter(is_published=True, **by_title_6x9).first()
        assets = [a for a in [a4, x69] if a]

    for asset in assets:
        dl_url = asset.get_download_url() if hasattr(asset, "get_download_url") else None
        if not dl_url:
            from django.urls import reverse
            dl_url = reverse("downloads:asset_download", kwargs={"slug": asset.slug})
        links.append(
            {
                "title": asset.title,
                "download_url": dl_url,
                "filesize": _filesize_display(asset),
            }
        )
    return links

