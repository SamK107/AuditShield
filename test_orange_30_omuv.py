#!/usr/bin/env python
"""
Test Orange Money avec 30 OMUV (solde disponible dans le compte de test).
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

def test_payment_30_omuv():
    """Test avec 30 OMUV (solde disponible: 33 OMUV)."""
    print("\n" + "="*80)
    print(" TEST ORANGE MONEY - 30 OMUV (Solde disponible)")
    print("="*80)
    
    product = Product.objects.filter(is_published=True).first()
    
    # Créer un Order avec 30 OMUV
    test_order = Order(
        product=product,
        amount_fcfa=30,  # 30 OMUV - dans la limite du solde disponible
        currency="XOF",
        status="PENDING",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        phone="7701101166",
    )
    test_order.save()
    
    print(f"\n✅ Order créé: ID={test_order.id}")
    print(f"  Montant: 30 OMUV (Solde disponible: 33 OMUV)")
    
    try:
        result = orange_money.create_payment_request(test_order)
        
        print(f"\n✅ Paiement initialisé avec succès!")
        print(f"\n🔗 URL de paiement:")
        print(f"  {result['payment_url']}")
        print(f"\n📝 Instructions:")
        print(f"  1. Ouvrir l'URL ci-dessus")
        print(f"  2. Entrer MSISDN: 7701101166")
        print(f"  3. Entrer PIN: 4940")
        print(f"  4. Entrer le code USSD reçu")
        print(f"  5. Le paiement devrait RÉUSSIR cette fois! ✅")
        print(f"\n💰 Solde après paiement: 33 - 30 = 3 OMUV restants")
        
        # Ne pas supprimer l'Order - on veut tester le paiement réel
        print(f"\n⚠️  Order {test_order.id} conservé pour tester le paiement complet")
        print(f"  Supprimez-le manuellement après le test si nécessaire:")
        print(f"  python manage.py shell -c \"from store.models import Order; Order.objects.get(id={test_order.id}).delete()\"")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        test_order.delete()
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    try:
        result = test_payment_30_omuv()
        if result:
            print("\n" + "="*80)
            print(" ✅ TEST RÉUSSI - Testez le paiement dans le navigateur!")
            print("="*80)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

