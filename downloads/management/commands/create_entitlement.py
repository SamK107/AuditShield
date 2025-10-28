import os
from django.core.management.base import BaseCommand, CommandError
from downloads.models import ExternalEntitlement, DownloadCategory


class Command(BaseCommand):
    help = "Crée un ExternalEntitlement pour un achat externe"

    def add_arguments(self, parser):
        parser.add_argument('order_ref', type=str, help='Référence de commande (ex: EXT-7777)')
        parser.add_argument('email', type=str, help='Email du client')
        parser.add_argument('--category', type=str, default='ebook', help='Slug de la catégorie (défaut: ebook)')
        parser.add_argument('--platform', type=str, default='external', help='Plateforme (défaut: external)')

    def handle(self, *args, **options):
        order_ref = options['order_ref'].strip()
        email = options['email'].strip().lower()
        category_slug = options['category']
        platform = options['platform']

        # Vérifier la catégorie
        category = DownloadCategory.objects.filter(slug=category_slug).first()
        if not category:
            self.stdout.write(self.style.ERROR(f"Catégorie '{category_slug}' introuvable !"))
            self.stdout.write("Catégories disponibles:")
            for cat in DownloadCategory.objects.all():
                self.stdout.write(f"  - {cat.slug} ({cat.title})")
            raise CommandError("Catégorie invalide")

        # Créer ou récupérer l'entitlement
        ent, created = ExternalEntitlement.objects.get_or_create(
            email=email,
            category=category,
            platform=platform,
            order_ref=order_ref,
            defaults={}
        )

        if created:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Entitlement créé: {order_ref} | {email} | {category_slug}"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"ℹ️  Entitlement existe déjà: {order_ref} | {email} | {category_slug}"
            ))

