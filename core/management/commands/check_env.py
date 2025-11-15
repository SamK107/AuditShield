from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = "Affiche les principales variables d'environnement configurées"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Vérification des variables d'environnement ==="))
        self.stdout.write(f"CELERY_BROKER_URL : {os.getenv('CELERY_BROKER_URL')}")
        self.stdout.write(f"SITE_URL          : {os.getenv('SITE_URL')}")
        openai = os.getenv('OPENAI_API_KEY')
        if openai:
            self.stdout.write("OPENAI_API_KEY    : OK Defini (masque pour securite)")
        else:
            self.stdout.write(self.style.WARNING("OPENAI_API_KEY    : Non defini"))

