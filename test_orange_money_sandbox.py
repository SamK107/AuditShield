#!/usr/bin/env python
"""
Script de test standalone pour Orange Money WebPay DEV (Sandbox).
Conforme au guide officiel Orange Money WebPay Dev.

Usage:
    python test_orange_money_sandbox.py
    
Prérequis:
    - Variables d'environnement configurées dans .env
    - Django configuré (DJANGO_SETTINGS_MODULE)
"""
import os
import sys
import django
import json
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH pour importer les modules du projet
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configurer Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# Initialiser Django
django.setup()

# Maintenant on peut importer les modules Django
from store.services import orange_money
from store.models import Product, Order
from django.conf import settings


def print_header(title: str):
    """Affiche un header formaté."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_config():
    """Affiche la configuration Orange Money."""
    print_header("Configuration Orange Money")
    
    config_vars = {
        "ORANGE_CLIENT_ID": settings.ORANGE_CLIENT_ID,
        "ORANGE_CLIENT_SECRET": settings.ORANGE_CLIENT_SECRET,
        "ORANGE_APPLICATION_ID": settings.ORANGE_APPLICATION_ID,
        "ORANGE_OAUTH_TOKEN_URL": settings.ORANGE_OAUTH_TOKEN_URL,
        "ORANGE_WEBPAY_DEV_URL": settings.ORANGE_WEBPAY_DEV_URL,
        "ORANGE_MERCHANT_KEY": settings.ORANGE_MERCHANT_KEY,
        "ORANGE_MERCHANT_MSISDN": settings.ORANGE_MERCHANT_MSISDN,
        "ORANGE_MERCHANT_AGENT_CODE": settings.ORANGE_MERCHANT_AGENT_CODE,
        "ORANGE_RETURN_URL": settings.ORANGE_RETURN_URL,
        "ORANGE_CANCEL_URL": settings.ORANGE_CANCEL_URL,
        "ORANGE_NOTIFY_URL": settings.ORANGE_NOTIFY_URL,
    }
    
    for key, value in config_vars.items():
        # Masquer les secrets (garder seulement les 4 premiers caractères)
        if any(secret in key.lower() for secret in ["secret", "key"]) and value:
            masked_value = f"{value[:4]}***masked***" if len(value) > 4 else "***masked***"
            print(f"  {key}: {masked_value}")
        else:
            print(f"  {key}: {value or '❌ Non défini'}")
    
    # Vérifier les variables essentielles
    required = {
        "ORANGE_CLIENT_ID": settings.ORANGE_CLIENT_ID,
        "ORANGE_CLIENT_SECRET": settings.ORANGE_CLIENT_SECRET,
        "ORANGE_MERCHANT_KEY": settings.ORANGE_MERCHANT_KEY,
    }
    missing = [key for key, val in required.items() if not val]
    
    if missing:
        print("\n⚠️  ATTENTION: Variables manquantes:")
        for key in missing:
            print(f"  - {key}")
        print("\nConfigurer ces variables dans le fichier .env avant de continuer.")
        return False
    
    print("\n✅ Configuration valide")
    return True


def test_oauth_token():
    """Teste l'obtention du token OAuth."""
    print_header("Test 1: Obtention du token OAuth")
    
    try:
        print("Appel de l'API OAuth...")
        token = orange_money.get_access_token()
        
        print("✅ Token obtenu avec succès!")
        print(f"  Token (masqué): {token[:20]}***")
        return token
    
    except orange_money.OrangeMoneyAuthError as e:
        print(f"❌ Erreur d'authentification OAuth: {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_webpay_init():
    """Teste l'initialisation d'un paiement WebPay."""
    print_header("Test 2: Initialisation d'un paiement WebPay")
    
    try:
        # Créer un Order de test
        print("Création d'un Order de test...")
        
        # Récupérer un produit existant ou en créer un fictif
        product = Product.objects.filter(is_published=True).first()
        if not product:
            print("⚠️  Aucun produit publié trouvé. Création d'un Order sans produit...")
            product = None
        
        # Créer un Order temporaire pour le test
        test_order = Order(
            product=product,
            amount_fcfa=1000,  # 1000 FCFA pour le test
            currency="XOF",
            status="PENDING",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            phone=settings.ORANGE_TEST_SUBSCRIBER_MSISDN,
        )
        
        # Sauvegarder l'Order pour obtenir un ID et un UUID
        test_order.save()
        
        print(f"  Order créé: ID={test_order.id}, UUID={test_order.uuid}")
        print(f"  Montant: {test_order.amount_fcfa} XOF")
        
        # Appeler l'API Orange Money pour créer le paiement
        print("\nAppel de l'API Orange Money WebPay...")
        result = orange_money.create_payment_request(test_order)
        
        print("\n✅ Paiement initialisé avec succès!")
        print(f"  Status: {result.get('raw_response', {}).get('status', 'N/A')}")
        print(f"  Order ID: {result.get('order_id')}")
        print(f"  Pay Token (masqué): {result.get('pay_token', '')[:20]}***")
        print(f"  Notif Token (masqué): {result.get('notif_token', '')[:20] if result.get('notif_token') else 'N/A'}***")
        print(f"  Payment URL: {result.get('payment_url')}")
        
        # Afficher la réponse complète (masquée)
        print("\n📄 Réponse API complète:")
        raw_response = result.get('raw_response', {})
        # Masquer les tokens avant affichage
        display_response = orange_money._mask_sensitive_data(raw_response, ["token"])
        print(json.dumps(display_response, indent=2, ensure_ascii=False))
        
        # Nettoyer: supprimer l'Order de test
        print(f"\nNettoyage: suppression de l'Order de test (ID={test_order.id})...")
        test_order.delete()
        
        return result
    
    except orange_money.OrangeMoneyAuthError as e:
        print(f"❌ Erreur d'authentification OAuth: {e}")
        # Nettoyer si l'order existe
        if 'test_order' in locals() and test_order.id:
            test_order.delete()
        return None
    except orange_money.OrangeMoneyAPIError as e:
        print(f"❌ Erreur API Orange Money: {e}")
        if hasattr(e, 'status_code'):
            print(f"  Status Code: {e.status_code}")
        if hasattr(e, 'response_data'):
            print(f"  Response Data: {json.dumps(e.response_data, indent=2, ensure_ascii=False)}")
        # Nettoyer si l'order existe
        if 'test_order' in locals() and test_order.id:
            test_order.delete()
        return None
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        # Nettoyer si l'order existe
        if 'test_order' in locals() and test_order.id:
            test_order.delete()
        return None


def main():
    """Point d'entrée principal du script de test."""
    print_header("Test Orange Money WebPay DEV - Sandbox")
    print("Script de test standalone pour l'intégration Orange Money.")
    print("Environnement: " + os.getenv("DJANGO_SETTINGS_MODULE", "Non défini"))
    
    # 1. Afficher et valider la configuration
    if not print_config():
        print("\n❌ Configuration invalide. Arrêt du test.")
        sys.exit(1)
    
    # 2. Tester l'obtention du token OAuth
    token = test_oauth_token()
    if not token:
        print("\n❌ Échec du test OAuth. Arrêt du test.")
        sys.exit(1)
    
    # 3. Tester l'initialisation d'un paiement WebPay
    result = test_webpay_init()
    if not result:
        print("\n❌ Échec du test WebPay. Arrêt du test.")
        sys.exit(1)
    
    # Résumé final
    print_header("Résumé des tests")
    print("✅ Test OAuth: OK")
    print("✅ Test WebPay Init: OK")
    print(f"\n🔗 URL de paiement sandbox:")
    print(f"  {result.get('payment_url')}")
    print("\n📝 Pour tester le paiement complet:")
    print("  1. Ouvrir l'URL ci-dessus dans un navigateur")
    print("  2. Entrer le numéro de test: " + settings.ORANGE_TEST_SUBSCRIBER_MSISDN)
    print("  3. Entrer le PIN de test: " + settings.ORANGE_TEST_SUBSCRIBER_PIN)
    print("  4. Valider le paiement")
    print("\n✅ Tests terminés avec succès!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

