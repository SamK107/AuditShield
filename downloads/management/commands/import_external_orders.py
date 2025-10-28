import csv
from django.core.management.base import BaseCommand, CommandError
from downloads.models import ExternalEntitlement, DownloadCategory

# CSV attendu: email,category_slug,platform,order_ref,claim_code
# - category_slug: ex. bonus | checklists | outils-pratiques | irregularites
# - platform: publiseer|youscribe|chariow|other

class Command(BaseCommand):
    help = "Importe des achats externes (CSV) et crée les entitlements pour l'accès aux téléchargements."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Chemin vers le CSV")

    def handle(self, *args, **opts):
        path = opts["csv_path"]
        created = 0
        with open(path, newline="", encoding="utf-8") as f:
            for i, row in enumerate(csv.DictReader(f), start=1):
                email = (row.get("email") or "").strip().lower()
                slug = (row.get("category_slug") or "").strip()
                platform = (row.get("platform") or "other").strip().lower()
                order_ref = (row.get("order_ref") or "").strip()
                claim_code = (row.get("claim_code") or "").strip() or None

                if not email or not slug:
                    self.stdout.write(self.style.WARNING(f"[L{i}] ignorée (email/slug manquant)"))
                    continue

                cat = DownloadCategory.objects.filter(slug=slug).first()
                if not cat:
                    self.stdout.write(self.style.WARNING(f"[L{i}] catégorie inconnue: {slug}"))
                    continue

                obj, is_new = ExternalEntitlement.objects.get_or_create(
                    email=email, category=cat, platform=platform, order_ref=order_ref or None,
                    defaults={"claim_code": claim_code},
                )
                created += 1 if is_new else 0

        self.stdout.write(self.style.SUCCESS(f"Import terminé. Nouveaux enregistrements: {created}"))
