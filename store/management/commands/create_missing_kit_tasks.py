"""
Commande pour créer les KitProcessingTask manquantes pour les ClientInquiry existants.
Utile pour rétro-ajouter les tâches après la correction du bug.
"""
from django.core.management.base import BaseCommand
from store.models import ClientInquiry, KitProcessingTask


class Command(BaseCommand):
    help = "Crée les KitProcessingTask manquantes pour les ClientInquiry de type KIT"

    def handle(self, *args, **options):
        inquiries = ClientInquiry.objects.filter(kind=ClientInquiry.KIND_KIT)
        created = 0
        
        for inquiry in inquiries:
            # Vérifier si une tâche existe déjà
            if not KitProcessingTask.objects.filter(inquiry=inquiry).exists():
                KitProcessingTask.objects.create(
                    inquiry=inquiry,
                    status="PENDING"
                )
                created += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Tâche créée pour inquiry {inquiry.id} ({inquiry.email})")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⏭️  Tâche déjà existante pour inquiry {inquiry.id}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ {created} tâche(s) créée(s) sur {inquiries.count()} inquiry(s)")
        )

