# store/models.py
import uuid

from django.core.validators import EmailValidator
from django.db import models
from django.utils import timezone


def get_expires_at():
    # 72h par défaut
    return timezone.now() + timezone.timedelta(hours=72)

class Product(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    price_fcfa = models.PositiveIntegerField(default=15000)
    hero_image = models.ImageField(upload_to="products/", blank=True, null=True)
    guarantee_text = models.TextField(blank=True)
    faq_json = models.JSONField(default=list, blank=True)
    social_proofs_json = models.JSONField(default=list, blank=True)
    deliverable_file = models.FileField(upload_to="deliverables/", blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    download_slug = models.SlugField(
        null=True,
        blank=True,
        help_text="Slug de l'asset à télécharger (app 'downloads').",
    )

    def __str__(self):
        return self.title

class OfferTier(models.Model):
    STANDARD = "STANDARD"
    PERSONNALISATION = "PERSONNALISATION"
    FORMATION = "FORMATION"
    KIND_CHOICES = [
        (STANDARD, "Standard"),
        (PERSONNALISATION, "Personnalisation"),
        (FORMATION, "Formation & Assistance"),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    title = models.CharField(max_length=200, blank=True)  # Ajouté pour affichage/seed
    price_fcfa = models.PositiveIntegerField(blank=True, null=True)
    description_md = models.TextField(blank=True)
    cta_type = models.CharField(max_length=10, default="BUY")  # BUY|QUOTE|CALL

    class Meta:
        unique_together = ("product", "kind")

    def __str__(self):
        return f"{self.product.title} - {self.kind}"

class ExampleSlide(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="examples")
    title = models.CharField(max_length=200)
    irregularity = models.TextField()
    indicators = models.TextField(blank=True)
    legal_ref = models.CharField(max_length=300, blank=True)
    remedy = models.TextField()
    risks = models.TextField(blank=True)
    sample_doc_url = models.URLField(blank=True)
    image = models.ImageField(upload_to="examples/", blank=True, null=True)
    order = models.PositiveSmallIntegerField(default=0, db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("order", "id")

class MediaAsset(models.Model):
    PDF_EXTRACT = "PDF_EXTRACT"
    VIDEO = "VIDEO"
    KIND_CHOICES = [(PDF_EXTRACT, "PDF extrait"), (VIDEO, "Vidéo")]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    title = models.CharField(max_length=200)
    file_or_url = models.CharField(max_length=500)
    thumb = models.ImageField(upload_to="media/thumbs/", blank=True, null=True)

    def __str__(self):
        return f"{self.product.title} - {self.kind}: {self.title}"

class Order(models.Model):
    STATUS_CHOICES = [
        ("CREATED", "Créée"),
        ("PENDING", "En attente"),
        ("PAID", "Payée"),
        ("FAILED", "Échouée"),
        ("CANCELED", "Annulée"),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    # Pour compatibilité, à remplacer par tier FK si Tier existe
    tier_id = models.IntegerField(null=True, blank=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)

    amount_fcfa = models.PositiveIntegerField()
    currency = models.CharField(max_length=8, default="XOF")

    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="CREATED")

    cinetpay_payment_id = models.CharField(max_length=100, blank=True)
    provider_ref = models.CharField(max_length=64, unique=True, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order#{self.pk} - {self.product} - {self.email}"

    @property
    def amount_xof(self) -> int:
        """Compat pour anciens appels CinetPay qui lisaient amount_xof."""
        return self.amount_fcfa

class DownloadToken(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField(default=get_expires_at)

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Token for {self.order.order_id}"

# --- NOUVEAU : Catégories (par fonction/structure) ---
class IrregularityCategory(models.Model):
    FUNCTION = "FUNCTION"
    STRUCTURE = "STRUCTURE"
    GROUP_CHOICES = [(FUNCTION, "Fonction"), (STRUCTURE, "Structure")]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="ir_categories")
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    group = models.CharField(max_length=16, choices=GROUP_CHOICES, default=STRUCTURE)
    order = models.PositiveSmallIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("product", "slug")
        ordering = ("order", "title")

    def __str__(self):
        return f"{self.title} ({self.get_group_display()})"

# --- Adapté : lignes du tableau rattachées à une catégorie ---
class IrregularityRow(models.Model):
    EBOOK = "EBOOK"
    PLUS = "PLUS"
    VERSION_CHOICES = [(EBOOK, "Version ebook"), (PLUS, "Version améliorée")]

    # (optionnel) héritage legacy : on garde product nullable pour compat
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="irregularity_rows",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        IrregularityCategory,
        on_delete=models.CASCADE,
        related_name="rows",
        null=True,
        blank=True,
    )

    version = models.CharField(max_length=10, choices=VERSION_CHOICES, default=EBOOK)
    irregularity = models.TextField(help_text="Irrégularité constatée")
    reference = models.CharField(max_length=255, blank=True, help_text="Référence juridique/texte")
    actors = models.CharField(max_length=255, blank=True, help_text="Acteurs concernés")
    dispositions = models.TextField(help_text="Dispositions pratiques/recommandations")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def __str__(self):
        return f"[{self.version}] {self.category.title} – {self.irregularity[:40]}..."


# --- Analyses préliminaires (tables -> lignes) ---

class PreliminaryTable(models.Model):
    STRUCTURE = "STRUCTURE"
    FONCTION = "FONCTION"
    GROUP_CHOICES = [
        (STRUCTURE, "Structure"),
        (FONCTION, "Fonction"),
    ]

    product = models.ForeignKey(
        "store.Product",
        on_delete=models.CASCADE,
        related_name="prelim_tables",
        null=True,
        blank=True,
    )
    slug = models.SlugField(max_length=80)
    title = models.CharField(max_length=200)
    group = models.CharField(max_length=12, choices=GROUP_CHOICES, default=STRUCTURE)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "slug")
        ordering = ("order", "title")
        verbose_name = "Table d'analyse préliminaire"
        verbose_name_plural = "Tables d'analyse préliminaire"

    def __str__(self):
        return self.title


class PreliminaryRow(models.Model):
    table = models.ForeignKey(PreliminaryTable, on_delete=models.CASCADE, related_name="rows")
    order = models.PositiveSmallIntegerField(default=0)
    irregularity = models.CharField("Irrégularité", max_length=255)
    reference = models.CharField("Référence", max_length=255, blank=True)
    actors = models.CharField("Acteurs concernés", max_length=255, blank=True)
    dispositions = models.TextField("Dispositions pratiques")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order", "id")
        verbose_name = "Ligne d'analyse préliminaire"
        verbose_name_plural = "Lignes d'analyse préliminaire"

    def __str__(self):
        return self.irregularity[:80]

# --- AJOUTS : demandes clients (Kit / Formation) ---
try:
    from django.db.models import JSONField  # Django 3.1+
except Exception:
    from django.contrib.postgres.fields import JSONField  # fallback

class ClientInquiry(models.Model):
    KIND_KIT = "KIT"
    KIND_TRAINING = "TRAINING"
    KIND_CHOICES = (
        (KIND_KIT, "Kit personnalisé"),
        (KIND_TRAINING, "Formation & Assistance"),
    )

    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=24, default="new")

    # Contact
    contact_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(validators=[EmailValidator()], blank=True)
    phone = models.CharField(max_length=64, blank=True)

    # Structure
    organization_name = models.CharField(max_length=180, blank=True)
    statut_juridique = models.CharField(max_length=48, blank=True)
    location = models.CharField(max_length=120, blank=True)
    sector = models.CharField(max_length=64, blank=True)
    mission_text = models.TextField(blank=True)

    # Ressources / budget
    budget_range = models.CharField(max_length=64, blank=True)
    funding_sources = JSONField(default=list, blank=True)

    # Audits / contrôles
    audits_types = JSONField(default=list, blank=True)
    audits_frequency = models.CharField(max_length=64, blank=True)

    # Organisation
    staff_size = models.CharField(max_length=32, blank=True)
    org_chart_text = models.TextField(blank=True)

    # Notes diverses
    notes_text = models.TextField(blank=True)

    # Payload brut du formulaire
    payload = JSONField(default=dict, blank=True)

    def __str__(self):
        who = self.organization_name or self.contact_name or self.email or str(self.pk)
        return f"{self.get_kind_display()} – {who}"


def upload_inquiry_doc(instance, filename):
    return f"inquiries/{instance.inquiry_id}/{filename}"

class InquiryDocument(models.Model):
    inquiry = models.ForeignKey(ClientInquiry, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to=upload_inquiry_doc)
    original_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name or (self.file.name.split('/')[-1])


# --- Paiement CinetPay ---
class Payment(models.Model):
    # Go/No-Go: order_id unique, provider_tx_id unique (nullable), status choices, updated_at
    order_id = models.CharField(max_length=64, unique=True)
    provider_tx_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    status = models.CharField(max_length=16, choices=[
        ("INIT", "INIT"),
        ("PENDING", "PENDING"),
        ("PAID", "PAID"),
        ("FAILED", "FAILED"),
        ("CANCELED", "CANCELED")
    ], default="INIT")
    amount = models.IntegerField()
    currency = models.CharField(max_length=8, default="XOF")
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.order_id} ({self.status})"

class PaymentEvent(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="events")
    kind = models.CharField(max_length=32)  # INIT, WEBHOOK, CHECK_OK, DELIVERED, ERROR, etc.
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Event {self.kind} for {self.payment.order_id} at {self.created_at}"