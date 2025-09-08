from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AssetCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.name


class DownloadableAsset(models.Model):
    VISIBILITY = (
        ("PUBLIC", "Public"),
        ("CUSTOMER_ONLY", "Clients seulement"),
        ("INTERNAL", "Interne"),
    )

    # --- Métadonnées
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=240, unique=True, blank=True)
    category = models.ForeignKey(
        AssetCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    description = models.TextField(blank=True)

    # --- Placement éditorial (immédiat)
    ebook_code = models.CharField(max_length=80, default="AUDIT_SANS_PEUR")
    part_code = models.CharField(max_length=80, blank=True)
    chapter_code = models.CharField(max_length=80, blank=True)

    # --- Lien générique optionnel (Chapter/Section/Article)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.CharField(max_length=64, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # --- Fichier
    file = models.FileField(upload_to="downloads/%Y/%m/")
    mime_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.BigIntegerField(default=0)

    # --- Qualité & sécurité
    sha256 = models.CharField(max_length=64, blank=True)
    antivirus_ok = models.BooleanField(default=True)

    # --- Cycle de vie
    version = models.CharField(max_length=40, default="1.0.0")
    is_deprecated = models.BooleanField(default=False)
    # replaced_by supprimé définitivement

    # --- Accès & statut
    visibility = models.CharField(
        max_length=20, choices=VISIBILITY, default="PUBLIC"
    )
    is_active = models.BooleanField(default=True)

    # --- Traçabilité
    download_count = models.PositiveIntegerField(default=0)
    last_download_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["ebook_code", "part_code", "chapter_code", "is_active"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    # def clean(self):
    #     # Validation pour éviter qu'un asset ne se remplace lui-même (champ supprimé)

    def __str__(self):
        return f"{self.title} (v{self.version})"



class AssetEvent(models.Model):
    asset = models.ForeignKey(
        DownloadableAsset, on_delete=models.CASCADE, related_name="events"
    )
    kind = models.CharField(
        max_length=40  # CLICK, DOWNLOAD, ERROR, VIRUS, REPLACED
    )
    at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(), null=True, blank=True, on_delete=models.SET_NULL
    )
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    utm_source = models.CharField(max_length=80, blank=True)
    utm_medium = models.CharField(max_length=80, blank=True)
    utm_campaign = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"{self.asset} - {self.kind} - {self.at}"

