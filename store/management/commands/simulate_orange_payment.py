# store/management/commands/simulate_orange_payment.py
"""
Commande pour simuler un paiement Orange Money réussi
Sans utiliser les crédits OMUV du sandbox

Usage:
    python manage.py simulate_orange_payment
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from store.models import Order, Product, DownloadToken
import uuid


class Command(BaseCommand):
    help = 'Simule un paiement Orange Money réussi pour tester les pages de retour'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write("🧪 Simulation Paiement Orange Money Réussi")
        self.stdout.write("="*60 + "\n")
        
        # Créer l'Order
        order = self.create_test_order()
        if not order:
            return
        
        self.stdout.write("")
        
        # Créer le DownloadToken
        token = self.create_download_token(order)
        
        # Afficher les URLs de test
        self.display_test_urls(order, token)
        
        # Instructions supplémentaires
        self.stdout.write("\n📋 POUR NETTOYER APRÈS LES TESTS :")
        self.stdout.write("   python manage.py shell")
        self.stdout.write("   >>> from store.models import Order")
        self.stdout.write("   >>> Order.objects.filter(email='test-orange@example.com').delete()")
        self.stdout.write("")

    def create_test_order(self):
        """Crée un Order de test marqué comme PAID"""
        
        # Récupérer le produit "Audit Sans Peur"
        product = Product.objects.filter(is_published=True).first()
        
        if not product:
            self.stdout.write(self.style.ERROR("❌ Aucun produit publié trouvé!"))
            self.stdout.write("   Créez d'abord un produit dans l'admin Django.")
            return None
        
        # Créer l'Order
        order = Order.objects.create(
            product=product,
            email="test-orange@example.com",
            first_name="Test",
            last_name="Orange Money",
            phone="+22370123456",
            amount_fcfa=15000,
            currency="XOF",
            status="PAID",  # Directement PAID
            paid_at=timezone.now(),
        )
        
        # Le provider_ref est généré automatiquement via save()
        self.stdout.write(self.style.SUCCESS(f"✅ Order créé: #{order.id}"))
        self.stdout.write(f"   UUID: {order.uuid}")
        self.stdout.write(f"   Provider Ref: {order.provider_ref}")
        self.stdout.write(f"   Email: {order.email}")
        self.stdout.write(f"   Status: {order.status}")
        self.stdout.write(f"   Montant: {order.amount_fcfa} FCFA")
        
        return order

    def create_download_token(self, order):
        """Crée un DownloadToken pour l'Order"""
        
        # Générer un token unique
        token_value = f"TEST-{uuid.uuid4().hex[:16]}"
        
        # Expiration dans 72h
        expires_at = timezone.now() + timedelta(hours=72)
        
        # Créer le token
        token = DownloadToken.objects.create(
            order=order,
            token=token_value,
            expires_at=expires_at,
            max_uses=999,  # Illimité pour les tests
            used_count=0,
        )
        
        self.stdout.write(self.style.SUCCESS("✅ DownloadToken créé"))
        self.stdout.write(f"   Token: {token.token}")
        self.stdout.write(f"   Expire le: {token.expires_at}")
        self.stdout.write(f"   Valide: {token.is_valid()}")
        
        return token

    def display_test_urls(self, order, token):
        """Affiche les URLs de test"""
        
        base_url = "http://127.0.0.1:8000"
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.WARNING("🎯 URLS DE TEST - Copiez/collez dans votre navigateur"))
        self.stdout.write("="*60)
        
        # URL de retour (page de succès)
        return_url = f"{base_url}/payments/om/return/?order_id={order.provider_ref}"
        self.stdout.write(self.style.SUCCESS(f"\n1️⃣  PAGE DE SUCCÈS (orange_success.html)"))
        self.stdout.write(f"    {return_url}")
        self.stdout.write("    ✓ Devrait afficher la page de succès avec les 3 boutons")
        
        # URL de téléchargement sécurisée (avec token)
        download_url = f"{base_url}/downloads/secure/{order.uuid}/{token.token}/"
        self.stdout.write(self.style.SUCCESS(f"\n2️⃣  PAGE DE TÉLÉCHARGEMENT (2 formats PDF)"))
        self.stdout.write(f"    {download_url}")
        self.stdout.write("    ✓ Accès direct avec token (pas besoin de session)")
        
        # URL de téléchargement sécurisée (sans token, via session)
        download_url_session = f"{base_url}/downloads/secure/{order.uuid}/"
        self.stdout.write(self.style.SUCCESS(f"\n3️⃣  PAGE DE TÉLÉCHARGEMENT (via session)"))
        self.stdout.write(f"    {download_url_session}")
        self.stdout.write("    ✓ Nécessite d'être venu depuis la page de succès (session)")
        
        # URL des ressources bonus
        resources_url = f"{base_url}/downloads/resources/{order.uuid}/"
        self.stdout.write(self.style.SUCCESS(f"\n4️⃣  PAGE RESSOURCES BONUS"))
        self.stdout.write(f"    {resources_url}")
        self.stdout.write("    ✓ Checklists, outils, bonus, etc.")
        
        # URL pour tester l'annulation
        cancel_url = f"{base_url}/payments/om/cancel/?order_id={order.provider_ref}"
        self.stdout.write(self.style.SUCCESS(f"\n5️⃣  PAGE D'ANNULATION (orange_cancel.html)"))
        self.stdout.write(f"    {cancel_url}")
        self.stdout.write("    ✓ Simule un paiement annulé")
        
        # URL pour tester "unknown"
        unknown_url = f"{base_url}/payments/om/return/"
        self.stdout.write(self.style.SUCCESS(f"\n6️⃣  PAGE ERREUR (orange_unknown.html)"))
        self.stdout.write(f"    {unknown_url}")
        self.stdout.write("    ✓ Sans paramètre order_id")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.WARNING("💡 CONSEIL : Commencez par tester l'URL 1 (page de succès)"))
        self.stdout.write("="*60 + "\n")
