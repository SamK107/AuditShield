from django.utils import timezone

try:
    from storages.backends.s3boto3 import S3Boto3Storage
    HAS_S3 = True
except Exception:
    HAS_S3 = False

from .models import DownloadableAsset


class SignedUrlService:
    @staticmethod
    def get_signed_url(asset: DownloadableAsset, *, expires=300) -> str:
        f = asset.file
        if not f:
            raise ValueError("File missing")
        if HAS_S3 and isinstance(f.storage, S3Boto3Storage):
            return f.storage.url(
                f.name,
                parameters={"ResponseContentDisposition": f"attachment; filename={f.name.split('/')[-1]}"},
                expire=expires,
            )
        return f.url

    @staticmethod
    def update_analytics(asset: DownloadableAsset, request, kind="DOWNLOAD"):
        asset.download_count = (asset.download_count or 0) + 1
        asset.last_download_at = timezone.now()
        asset.save(update_fields=["download_count", "last_download_at"])
        # AssetEvent n'existe plus, donc on ne log plus d'événement détaillé ici.


def user_has_access(request, category) -> bool:
    """Retourne True si la catégorie n'est pas protégée ou si l'utilisateur/email possède un droit (entitlement)."""
    if not getattr(category, "is_protected", False):
        return True
    from .models import DownloadEntitlement
    # Utilisateur connecté
    if getattr(request, "user", None) and request.user.is_authenticated:
        if DownloadEntitlement.objects.filter(user=request.user, category=category).exists():
            return True
        email = getattr(request.user, "email", None)
        if email and DownloadEntitlement.objects.filter(email=email, category=category).exists():
            return True
    # Fallback session (après claim par email)
    email = request.session.get("verified_email")
    if email and DownloadEntitlement.objects.filter(email=email, category=category).exists():
        return True
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

