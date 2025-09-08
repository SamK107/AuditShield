from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django import forms
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
    if asset.is_deprecated:
        raise Http404()
    if not _require_access(asset, request):
        raise Http404()
    url = SignedUrlService.get_signed_url(asset)
    SignedUrlService.update_analytics(asset, request, kind="DOWNLOAD")
    return HttpResponseRedirect(url)


def telecharger(request, slug):
    # Vue identique à asset_download mais pour l'URL courte
    asset = get_object_or_404(DownloadableAsset, slug=slug, is_active=True)
    if asset.is_deprecated:
        raise Http404()
    if not _require_access(asset, request):
        raise Http404()
    url = SignedUrlService.get_signed_url(asset)
    SignedUrlService.update_analytics(asset, request, kind="DOWNLOAD")
    return HttpResponseRedirect(url)


class DownloadableAssetForm(forms.ModelForm):
    class Meta:
        model = DownloadableAsset
        fields = [
            'title', 'category', 'description', 'file', 'tags',
            'ebook_code', 'part_code', 'chapter_code', 'visibility'
        ]


def asset_upload(request):
    if request.method == 'POST':
        form = DownloadableAssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.save()
            form.save_m2m()
            return redirect('downloads:asset_upload_success')
    else:
        form = DownloadableAssetForm()
    return render(request, 'downloads/asset_upload.html', {'form': form})


def asset_upload_success(request):
    return render(request, 'downloads/asset_upload_success.html')
