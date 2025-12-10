#!/usr/bin/env python
"""
Script de test pour créer une commande factice et tester la page de succès Orange Money
Sans consommer de crédit sandbox.

Usage:
    python test_orange_success_page.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from store.models import Order, Product, DownloadToken
from django.utils import timezone
from datetime import timedelta

def create_test_order():
    """Crée une commande de test pour tester la page de succès"""
    
    # Récupérer le premier produit publié
    product = Product.objects.filter(is_published=True).first()
    
    if not product:
        print("❌ Aucun produit publié trouvé!")
        print("   Créez d'abord un produit dans l'admin Django")
        return None
    
    # Créer une commande de test
    order = Order.objects.create(
        product=product,
        email="test@auditsanspeur.com",
        first_name="Test",
        last_name="Orange Money",
        phone="+22370123456",
        amount_fcfa=15000,
        currency="XOF",
        status="PAID",  # ✅ Déjà payée
        paid_at=timezone.now(),
    )
    
    print(f"✅ Commande de test créée : Order#{order.id}")
    print(f"   UUID: {order.uuid}")
    print(f"   Provider ref: {order.provider_ref}")
    print(f"   Email: {order.email}")
    print(f"   Status: {order.status}")
    
    # Créer un token de téléchargement
    token = DownloadToken.objects.create(
        order=order,
        token=f"TEST-TOKEN-{order.uuid.hex[:16]}",
        expires_at=timezone.now() + timedelta(days=30),
        max_uses=999,
        used_count=0,
    )
    
    print(f"✅ Token de téléchargement créé : {token.token}")
    
    return order

def main():
    print("=" * 70)
    print("🧪 CRÉATION D'UNE COMMANDE DE TEST POUR ORANGE MONEY")
    print("=" * 70)
    print()
    
    # Créer la commande
    order = create_test_order()
    
    if not order:
        return
    
    print()
    print("=" * 70)
    print("🎯 URLS DE TEST")
    print("=" * 70)
    print()
    
    base_url = "http://127.0.0.1:8000"
    
    # URL de retour (success)
    return_url = f"{base_url}/payments/om/return/?order_id={order.provider_ref}"
    print(f"✅ PAGE DE SUCCÈS (Return URL):")
    print(f"   {return_url}")
    print()
    
    # URL de téléchargement
    download_url = f"{base_url}/downloads/secure/{order.uuid}/"
    print(f"📥 PAGE DE TÉLÉCHARGEMENT:")
    print(f"   {download_url}")
    print()
    
    # URL ressources
    resources_url = f"{base_url}/downloads/resources/{order.uuid}/"
    print(f"🎁 PAGE RESSOURCES BONUS:")
    print(f"   {resources_url}")
    print()
    
    # URL d'annulation (pour tester aussi)
    cancel_url = f"{base_url}/payments/om/cancel/?order_id={order.provider_ref}"
    print(f"⚠️  PAGE D'ANNULATION (pour tester):")
    print(f"   {cancel_url}")
    print()
    
    print("=" * 70)
    print("📋 INSTRUCTIONS")
    print("=" * 70)
    print()
    print("1. Démarrez le serveur Django si ce n'est pas déjà fait :")
    print("   python manage.py runserver")
    print()
    print("2. Ouvrez un navigateur et collez l'URL de succès ci-dessus")
    print()
    print("3. Vous devriez voir la page professionnelle avec :")
    print("   ✓ Bannière verte 'Paiement confirmé 🎉'")
    print("   ✓ Bouton 'Accéder à la page de téléchargement'")
    print("   ✓ Bouton 'Voir les ressources bonus'")
    print("   ✓ Bouton 'M'envoyer à nouveau les liens'")
    print()
    print("4. Cliquez sur chaque bouton pour tester les liens")
    print()
    print("5. Pour tester la page d'annulation, utilisez l'URL cancel ci-dessus")
    print()
    print("=" * 70)
    print("🧹 NETTOYAGE (après les tests)")
    print("=" * 70)
    print()
    print("Pour supprimer cette commande de test :")
    print()
    print("python manage.py shell")
    print(f">>> from store.models import Order")
    print(f">>> Order.objects.filter(id={order.id}).delete()")
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()

