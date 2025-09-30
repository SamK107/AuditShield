from django.db import models

# Create your models here.


class LegalDocument(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    STATUS_CHOICES = [(DRAFT, "Brouillon"), (PUBLISHED, "Publié")]

    MENTIONS = "mentions"
    PRIVACY = "privacy"
    COOKIES = "cookies"
    DOC_TYPES = [
        (MENTIONS, "Mentions légales"),
        (PRIVACY, "Politique de confidentialité"),
        (COOKIES, "Politique Cookies"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    html_content = models.TextField(help_text="Contenu HTML sûr (tu le maîtrises).")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PUBLISHED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document légal"
        verbose_name_plural = "Documents légaux"

    def __str__(self):
        return f"{self.title} [{self.doc_type}]"
