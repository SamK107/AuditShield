# flake8: noqa
from django.core.management.base import BaseCommand

from downloads.models import DownloadCategory

SEED = [
    {"slug": "checklists", "page_path": "/checklists", "is_protected": True, "required_sku": "EBOOK_ASP"},
    {"slug": "bonus", "page_path": "/bonus", "is_protected": True, "required_sku": "EBOOK_ASP"},
    {"slug": "outils-pratiques", "page_path": "/outils-pratiques", "is_protected": True, "required_sku": "EBOOK_ASP"},
    {"slug": "irregularites", "page_path": "/irregularites", "is_protected": True, "required_sku": "EBOOK_ASP"},
]


class Command(BaseCommand):
    help = "Crée/MAJ les catégories publiques de téléchargement"

    def handle(self, *args, **kwargs):
        for c in SEED:
            obj, created = DownloadCategory.objects.update_or_create(
                slug=c["slug"],
                defaults={k: v for k, v in c.items() if k != "slug"},
            )
            self.stdout.write(self.style.SUCCESS(f"{'Créé' if created else 'MAJ'}: {obj}"))

