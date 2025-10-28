from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import models
from django.urls import reverse


def upload_to(instance, filename):
    dt = instance.created_at or datetime.now()
    return f"downloads/{dt:%Y/%m}/{filename}"


class DownloadCategory(models.Model):
    slug = models.SlugField(
        primary_key=True, help_text="Ex: checklists, bonus, irregularites, outils-pratiques"
    )
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=200, blank=True)
    page_path = models.CharField(
        max_length=80, unique=True, help_text="Chemin public (commence par /), ex: /checklists"
    )
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_protected = models.BooleanField(default=False)
    required_sku = models.CharField(
        max_length=64, blank=True, help_text="Code produit requis (ex: EBOOK_ASP)"
    )

    class Meta:
        ordering = ["order", "slug"]

    def __str__(self):
        return self.title


class DownloadableAsset(models.Model):
    """
    Fichiers téléchargeables (PDF/DOCX/XLSX/ZIP...) affichés en carte sur la
    page d'une catégorie.
    """

    category = models.ForeignKey(DownloadCategory, related_name="assets", on_delete=models.CASCADE)
    slug = models.SlugField(
        max_length=120, unique=True, help_text="Slug unique pour l'URL ex: plan-action-correctif"
    )
    title = models.CharField(max_length=200)
    short_desc = models.CharField("Description courte (1 phrase)", max_length=200, blank=True)
    file = models.FileField(upload_to=upload_to)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def extension(self) -> str:
        return (Path(self.file.name).suffix or "").lstrip(".").upper()

    def get_download_url(self):
        return reverse("downloads:asset_download", kwargs={"slug": self.slug})


class DownloadEntitlement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    email = models.EmailField()
    category = models.ForeignKey(DownloadCategory, on_delete=models.CASCADE)
    source = models.CharField(
        max_length=16,
        choices=[("SITE", "SITE"), ("EXT", "EXTERNAL"), ("MANUAL", "MANUAL")],
        default="SITE",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("email", "category")]

    def __str__(self):
        return f"{self.email} → {self.category.slug} ({self.source})"


class PurchaseClaim(models.Model):
    email = models.EmailField()
    platform = models.CharField(max_length=40)  # SITE, AMAZON, KOBO, APPLE, OTHER
    order_ref = models.CharField(max_length=80, blank=True)
    category = models.ForeignKey(DownloadCategory, on_delete=models.CASCADE)
    proof = models.FileField(upload_to="claims/%Y/%m/", blank=True)
    status = models.CharField(
        max_length=16,
        choices=[("NEW", "NEW"), ("APPROVED", "APPROVED"), ("REJECTED", "REJECTED")],
        default="NEW",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Claim {self.email} [{self.platform}] {self.category.slug} ({self.status})"

# --- Entitlements externes (achats réalisés hors du site) ---
class ExternalEntitlement(models.Model):
    PLATFORM_CHOICES = [
        ("publiseer", "Publiseer"),
        ("youscribe", "YouScribe Afrique"),
        ("chariow", "Chariow"),
        ("other", "Autre"),
    ]

    email = models.EmailField(db_index=True)
    category = models.ForeignKey("downloads.DownloadCategory", on_delete=models.CASCADE, related_name="external_entitlements")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default="other")
    order_ref = models.CharField(max_length=120, blank=True, null=True)  # ref commande plateformes
    claim_code = models.CharField(max_length=32, blank=True, null=True, db_index=True)  # optionnel
    created_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = [("email", "category", "platform", "order_ref")]
        verbose_name = "Droit d'accès externe"
        verbose_name_plural = "Droits d'accès externes"

    def __str__(self):
        return f"{self.email} -> {self.category.slug} ({self.platform})"
