# store/models.py
from django.db import models
from django.utils import timezone
import uuid

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

    def __str__(self):
        return self.title

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
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    STATUS_CHOICES = [(PENDING, "En attente"), (PAID, "Payé"), (FAILED, "Échec")]

    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    email = models.EmailField()
    amount_fcfa = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    cinetpay_payment_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.status}"

class DownloadToken(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField(default=get_expires_at)

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Token for {self.order.order_id}"
