import hashlib, mimetypes
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DownloadableAsset

@receiver(post_save, sender=DownloadableAsset)
def fill_meta_on_upload(sender, instance: DownloadableAsset, created, **kwargs):
    if not instance.file:
        return
    try:
        instance.size_bytes = instance.file.size
    except Exception:
        pass
    if not instance.mime_type:
        instance.mime_type = mimetypes.guess_type(instance.file.name)[0] or "application/octet-stream"
    try:
        hasher = hashlib.sha256()
        for chunk in instance.file.chunks():
            hasher.update(chunk)
        instance.sha256 = hasher.hexdigest()
    except Exception:
        pass
    instance.save(update_fields=["size_bytes", "mime_type", "sha256"])

