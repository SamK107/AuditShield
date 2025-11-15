from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import ClientInquiry
from store.tasks import build_kit_word


class Command(BaseCommand):
    help = "Traite la file d'attente du kit (fallback séquentiel si Celery indisponible)."

    def add_arguments(self, parser):
        parser.add_argument("--sample", action="store_true", help="Traiter un seul dossier (échantillon)")

    def handle(self, *args, **opts):
        sample = bool(opts.get("sample"))
        qs = ClientInquiry.objects.filter(payment_status="PAID").order_by("created_at")
        processed = 0
        for inquiry in qs:
            with transaction.atomic():
                # Éviter de relancer si déjà en cours/terminé
                if inquiry.processing_state not in ("PAID", "IA_RUNNING"):
                    continue
                # Exécuter directement la tâche
                build_kit_word(inquiry.id)
                processed += 1
            if sample and processed >= 1:
                break
        self.stdout.write(self.style.SUCCESS(f"Traités: {processed} dossier(s)"))


