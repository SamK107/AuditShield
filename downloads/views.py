from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from .models import DownloadableAsset
from .services import SignedUrlService

def _require_access(asset, request):
    if asset.visibility == "PUBLIC":
        return True
    if asset.visibility == "INTERNAL":
        return bool(request.user and request.user.is_staff)
    if asset.visibility == "CUSTOMER_ONLY":
        # À adapter: vérifier achat/abonnement côté store si nécessaire
        return bool(request.user and request.user.is_authenticated)
    return False

def asset_download(request, slug):
    asset = get_object_or_404(DownloadableAsset, slug=slug, is_active=True)
    if asset.is_deprecated and asset.replaced_by:
        asset = asset.replaced_by
    if not _require_access(asset, request):
        raise Http404()
    url = SignedUrlService.get_signed_url(asset)
    SignedUrlService.update_analytics(asset, request, kind="DOWNLOAD")
    return HttpResponseRedirect(url)
