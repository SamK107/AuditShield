"""
Commande pour vérifier si un email avec une référence de commande a été traité
Usage: python manage.py check_receipt EXT-7878
"""
from django.core.management.base import BaseCommand, CommandError
from downloads.models import ExternalEntitlement


class Command(BaseCommand):
    help = "Vérifie si une référence de commande (ex: EXT-7878) a été traitée dans receipts@"

    def add_arguments(self, parser):
        parser.add_argument(
            'order_ref',
            type=str,
            help='Référence de commande à vérifier (ex: EXT-7878)'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email optionnel pour filtrer les résultats'
        )

    def handle(self, *args, **opts):
        order_ref = opts['order_ref'].upper().strip()
        email_filter = opts.get('email', '').lower().strip() if opts.get('email') else None

        self.stdout.write(f"\n🔍 Recherche de la référence: {order_ref}")
        if email_filter:
            self.stdout.write(f"📧 Filtré par email: {email_filter}\n")

        # Recherche dans ExternalEntitlement
        query = ExternalEntitlement.objects.filter(order_ref__iexact=order_ref)
        
        if email_filter:
            query = query.filter(email__iexact=email_filter)

        results = list(query.order_by('-created_at'))

        if not results:
            self.stdout.write(self.style.ERROR(f"\n❌ Aucun entitlement trouvé pour la référence '{order_ref}'"))
            if email_filter:
                self.stdout.write(self.style.WARNING(f"   (filtré par email: {email_filter})"))
            
            self.stdout.write("\n📋 Actions suggérées:")
            self.stdout.write("   1. Vérifier si l'email est arrivé dans la boîte receipts@")
            self.stdout.write("   2. Exécuter: python manage.py fetch_receipts --all")
            self.stdout.write("   3. Vérifier les logs de fetch_receipts")
            return

        self.stdout.write(self.style.SUCCESS(f"\n✅ {len(results)} entitlement(s) trouvé(s):\n"))
        
        for i, ent in enumerate(results, 1):
            self.stdout.write(f"  [{i}] Référence: {ent.order_ref}")
            self.stdout.write(f"      Email: {ent.email}")
            self.stdout.write(f"      Catégorie: {ent.category.slug} ({ent.category.title})")
            self.stdout.write(f"      Plateforme: {ent.platform}")
            self.stdout.write(f"      Créé le: {ent.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if ent.redeemed_at:
                self.stdout.write(f"      Rédimé le: {ent.redeemed_at.strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write("")

        # Recherche partielle aussi
        partial = ExternalEntitlement.objects.filter(order_ref__icontains=order_ref)
        if len(partial) > len(results):
            self.stdout.write(self.style.WARNING(f"\n⚠️  Note: {len(partial)} entitlement(s) contiennent '{order_ref}' (recherche partielle)"))
            self.stdout.write("   Utilisez --email pour affiner la recherche\n")

