from django.core.management.base import BaseCommand

from downloads.models import DownloadCategory

CATS = [
    dict(
        slug="checklists",
        title="Check-lists d’audit prêtes à l’emploi",
        subtitle="Structures publiques, Projets financés, Collectivités",
        page_path="/checklists",
        order=1,
        is_protected=False,
        required_sku="",
    ),
    dict(
        slug="bonus",
        title="Bonus – Guide des réponses à l’audit",
        subtitle="Scripts de réponses factuelles aux constats",
        page_path="/bonus",
        order=2,
        is_protected=True,
        required_sku="EBOOK_ASP",
    ),
    dict(
        slug="outils-pratiques",
        title="Outils pratiques (modèles Word & Excel)",
        subtitle="Grilles Audit Rapport, Plan d’action correctif…",
        page_path="/outils-pratiques",
        order=3,
        is_protected=False,
        required_sku="",
    ),
    dict(
        slug="irregularites",
        title="Irrégularités fréquentes",
        subtitle="Tableaux par domaine et points de contrôle",
        page_path="/irregularites",
        order=4,
        is_protected=False,
        required_sku="",
    ),
]


class Command(BaseCommand):
    help = "Crée/MAJ les catégories publiques de téléchargement"

    def handle(self, *args, **kwargs):
        for c in CATS:
            obj, created = DownloadCategory.objects.update_or_create(
                slug=c["slug"],
                defaults={k: v for k, v in c.items() if k != "slug"},
            )
            self.stdout.write(
                self.style.SUCCESS(f"{'Créé' if created else 'MAJ'}: {obj}")
            )
