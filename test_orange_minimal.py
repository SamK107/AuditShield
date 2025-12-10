#!/usr/bin/env python
"""
Test Orange Money avec un montant minimal (1 OMUV).
"""
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from store.services import orange_money
from store.models import Product, Order

def test_minimal_payment():
    """Test avec 1 OMUV pour vérifier si c'est un problème de montant."""
    print("\n" + "="*80)
    print(" TEST ORANGE MONEY - MONTANT MINIMAL (1 OMUV)")
    print("="*80)
    
    # Créer un Order avec 1 OMUV
    product = Product.objects.filter(is_published=True).first()
    
    test_order = Order(
        product=product,
        amount_fcfa=1,  # 1 OMUV minimal
        currency="XOF",
        status="PENDING",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone="7701101166",
    )
    test_order.save()
    
    print(f"\n✅ Order créé: ID={test_order.id}, Montant=1 OMUV")
    
    try:
        result = orange_money.create_payment_request(test_order)
        print(f"\n✅ Paiement initialisé!")
        print(f"  Payment URL: {result['payment_url']}")
        print(f"\n🔗 Testez avec 1 OMUV:")
        print(f"  {result['payment_url']}")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
    finally:
        test_order.delete()
        print(f"\n✅ Order de test supprimé")

if __name__ == "__main__":
    test_minimal_payment()

