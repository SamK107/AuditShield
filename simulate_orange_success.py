#!/usr/bin/env python
"""
Script pour simuler un paiement Orange Money réussi
Sans utiliser les crédits OMUV du sandbox

Usage:
    python simulate_orange_success.py

Ce script va :
1. Créer un Order avec status PAID
2. Créer un DownloadToken
3. Afficher l'URL pour tester la page de succès
"""

import os
import sys
import django
from datetime import timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.utils import timezone
from store.models import Order, Product, DownloadToken
import uuid


def create_test_order():
    """Crée un Order de test marqué comme PAID"""
    
    # Récupérer le produit "Audit Sans Peur"
    product = Product.objects.filter(is_published=True).first()
    
    if not product:
        print("❌ Aucun produit publié trouvé!")
        print("   Créez d'abord un produit dans l'admin Django.")
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
    print(f"✅ Order créé: #{order.id}")
    print(f"   UUID: {order.uuid}")
    print(f"   Provider Ref: {order.provider_ref}")
    print(f"   Email: {order.email}")
    print(f"   Status: {order.status}")
    print(f"   Montant: {order.amount_fcfa} FCFA")
    
    return order


def create_download_token(order):
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
    
    print(f"✅ DownloadToken créé")
    print(f"   Token: {token.token}")
    print(f"   Expire le: {token.expires_at}")
    print(f"   Valide: {token.is_valid()}")
    
    return token


def display_test_urls(order, token):
    """Affiche les URLs de test"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("\n" + "="*60)
    print("🎯 URLS DE TEST - Copiez/collez dans votre navigateur")
    print("="*60)
    
    # URL de retour (page de succès)
    return_url = f"{base_url}/payments/om/return/?order_id={order.provider_ref}"
    print(f"\n1️⃣  PAGE DE SUCCÈS (orange_success.html)")
    print(f"    {return_url}")
    print(f"    ✓ Devrait afficher la page de succès avec les 3 boutons")
    
    # URL de téléchargement sécurisée (avec token)
    download_url = f"{base_url}/downloads/secure/{order.uuid}/{token.token}/"
    print(f"\n2️⃣  PAGE DE TÉLÉCHARGEMENT (2 formats PDF)")
    print(f"    {download_url}")
    print(f"    ✓ Accès direct avec token (pas besoin de session)")
    
    # URL de téléchargement sécurisée (sans token, via session)
    download_url_session = f"{base_url}/downloads/secure/{order.uuid}/"
    print(f"\n3️⃣  PAGE DE TÉLÉCHARGEMENT (via session)")
    print(f"    {download_url_session}")
    print(f"    ✓ Nécessite d'être venu depuis la page de succès (session)")
    
    # URL des ressources bonus
    resources_url = f"{base_url}/downloads/resources/{order.uuid}/"
    print(f"\n4️⃣  PAGE RESSOURCES BONUS")
    print(f"    {resources_url}")
    print(f"    ✓ Checklists, outils, bonus, etc.")
    
    # URL pour tester l'annulation
    cancel_url = f"{base_url}/payments/om/cancel/?order_id={order.provider_ref}"
    print(f"\n5️⃣  PAGE D'ANNULATION (orange_cancel.html)")
    print(f"    {cancel_url}")
    print(f"    ✓ Simule un paiement annulé")
    
    # URL pour tester "pending"
    print(f"\n6️⃣  PAGE EN ATTENTE (orange_pending.html)")
    print(f"    Pour tester : Créer un Order avec status='PENDING'")
    print(f"    puis accéder à : {base_url}/payments/om/return/?order_id=ORDER-xxx")
    
    # URL pour tester "unknown"
    unknown_url = f"{base_url}/payments/om/return/"
    print(f"\n7️⃣  PAGE ERREUR (orange_unknown.html)")
    print(f"    {unknown_url}")
    print(f"    ✓ Sans paramètre order_id")
    
    print("\n" + "="*60)
    print("💡 CONSEIL : Commencez par tester l'URL 1 (page de succès)")
    print("="*60 + "\n")


def main():
    print("\n" + "="*60)
    print("🧪 Simulation Paiement Orange Money Réussi")
    print("="*60 + "\n")
    
    # Créer l'Order
    order = create_test_order()
    if not order:
        return
    
    print()
    
    # Créer le DownloadToken
    token = create_download_token(order)
    
    # Afficher les URLs de test
    display_test_urls(order, token)
    
    # Instructions supplémentaires
    print("📋 POUR NETTOYER APRÈS LES TESTS :")
    print(f"   python manage.py shell")
    print(f"   >>> from store.models import Order")
    print(f"   >>> Order.objects.filter(email='test-orange@example.com').delete()")
    print()


if __name__ == "__main__":
    main()

