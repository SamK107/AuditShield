import mimetypes
from django.utils import timezone

try:
    from storages.backends.s3boto3 import S3Boto3Storage
    HAS_S3 = True
except Exception:
    HAS_S3 = False

from .models import DownloadableAsset, AssetEvent

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
        AssetEvent.objects.create(
            asset=asset,
            kind=kind,
            user=request.user if request and getattr(request, "user", None) and request.user.is_authenticated else None,
            ip=(request.META.get("REMOTE_ADDR") if request else None),
            user_agent=(request.META.get("HTTP_USER_AGENT") if request else ""),
            utm_source=getattr(request, "GET", {}).get("utm_source", ""),
            utm_medium=getattr(request, "GET", {}).get("utm_medium", ""),
            utm_campaign=getattr(request, "GET", {}).get("utm_campaign", ""),
        )

