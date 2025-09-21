import mimetypes
from pathlib import Path

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify

from .models import DownloadableAsset


def _set_if_exists(instance, attr: str, value):
    """
    N'assigne que si le champ existe vraiment sur le modèle et que la valeur actuelle est vide.
    Évite les AttributeError quand des champs legacy (mime_type, original_name, size) ont été retirés.
    """
    if hasattr(instance, attr):
        current = getattr(instance, attr, None)
        if (current is None or current == "") and value not in (None, ""):
            try:
                setattr(instance, attr, value)
            except Exception:
                # Tolérance maximum : ne jamais bloquer un upload
                pass

@receiver(pre_save, sender=DownloadableAsset)
def fill_meta_on_upload(sender, instance: DownloadableAsset, **kwargs):
    """
    Renseigne des métadonnées *si disponibles* et ne suppose pas l'existence de champs optionnels.
    """
    # 1) Slug auto si absent
    if not instance.slug:
        base = instance.title or Path(getattr(instance.file, "name", "")).stem or "asset"
        instance.slug = slugify(base)[:120]

    # 2) Métadonnées facultatives (uniquement si les champs existent encore)
    filename = Path(getattr(instance.file, "name", "")).name
    guessed_mime, _ = mimetypes.guess_type(filename)
    _set_if_exists(instance, "mime_type", guessed_mime or "")
    _set_if_exists(instance, "original_name", filename)
    _set_if_exists(instance, "size", getattr(instance.file, "size", None))

