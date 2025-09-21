from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from downloads.models import DownloadableAsset, DownloadCategory

SAMPLES = {
    "checklists": [
        ("Checklist – Structures publiques", "Points essentiels pour démarrer le contrôle", "checklist_publiques.txt", "Item 1\nItem 2\nItem 3\n".encode("utf-8")),
        ("Checklist – Projets financés", "Contrôles clés bailleurs", "checklist_projets.csv", "rubrique;test\nA;OK\nB;OK\n".encode("utf-8")),
    ],
    "bonus": [
        ("Guide des réponses – Version courte", "Exemples de réponses factuelles", "bonus_reponses.txt", "Q1: ...\nR1: ...\n".encode("utf-8")),
    ],
    "outils-pratiques": [
        ("Plan d’action correctif (exemple)", "Modèle simple à adapter", "plan_action.txt", "Action;Responsable;Échéance\n...".encode("utf-8")),
    ],
    "irregularites": [
        ("Irrégularités fréquentes (extrait)", "Tableau de synthèse", "irregs.csv", "domaine;constat\nProcédure;Absence visa\n".encode("utf-8")),
    ],
}

class Command(BaseCommand):
    help = "Crée quelques assets publiés avec fichiers factices"

    def handle(self, *args, **kwargs):
        created = 0
        for slug, items in SAMPLES.items():
            try:
                cat = DownloadCategory.objects.get(slug=slug)
            except DownloadCategory.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Catégorie '{slug}' manquante. Lancez 'seed_download_pages' d'abord."))
                continue
            for title, desc, fname, payload in items:
                a, is_new = DownloadableAsset.objects.get_or_create(
                    category=cat,
                    title=title,
                    defaults={"short_desc": desc, "slug": fname.replace('.', '-'), "is_published": True, "order": 10}
                )
                if is_new or not a.file:
                    a.file.save(fname, ContentFile(payload), save=True)
                created += 1 if is_new else 0
        self.stdout.write(self.style.SUCCESS(f"OK – assets créés/actualisés. Nouveaux: {created}"))
