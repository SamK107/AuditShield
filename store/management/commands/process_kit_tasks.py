"""
Commande de gestion pour traiter les tâches KitProcessingTask en PENDING
et produire un .docx à partir du prompt_md.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from pathlib import Path

from store.models import KitProcessingTask
from store.utils.docx_builder import build_docx_with_cover


class Command(BaseCommand):
    help = "Traite les tâches KitProcessingTask en PENDING et produit un .docx"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Nombre maximum de tâches à traiter (défaut: 5)',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        tasks = KitProcessingTask.objects.select_related("inquiry").filter(status="PENDING")[:limit]
        
        if not tasks.exists():
            self.stdout.write(self.style.WARNING("Aucune tâche PENDING à traiter."))
            return

        self.stdout.write(f"Traitement de {tasks.count()} tâche(s)...")

        for t in tasks:
            self.stdout.write(f"Traitement de la tâche {t.id}...")
            t.status = "RUNNING"
            t.started_at = timezone.now()
            t.save(update_fields=["status", "started_at"])

            try:
                # Utiliser prompt_md s'il existe, sinon re-render
                md_text = t.prompt_md
                if not md_text:
                    md_text = render_to_string("ai/prompts/kit_complet_consigne.md", {"inquiry": t.inquiry})
                    t.prompt_md = md_text
                    t.save(update_fields=["prompt_md"])

                # Générer le DOCX
                out_path = build_docx_with_cover(md_text)
                
                # Sauvegarder dans le FileField
                with open(out_path, "rb") as f:
                    t.word_file.save(Path(out_path).name, ContentFile(f.read()), save=False)

                t.status = "DONE"
                t.finished_at = timezone.now()
                t.save(update_fields=["status", "finished_at", "word_file"])

                self.stdout.write(self.style.SUCCESS(f"[OK] Task {t.id} - DOCX généré"))
                
                # Nettoyer le fichier temporaire
                try:
                    Path(out_path).unlink(missing_ok=True)
                except Exception:
                    pass

            except Exception as e:
                t.status = "FAILED"
                t.error = str(e)
                t.finished_at = timezone.now()
                t.save(update_fields=["status", "error", "finished_at"])
                self.stdout.write(self.style.ERROR(f"[ERR] Task {t.id}: {e}"))

