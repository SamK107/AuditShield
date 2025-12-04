#!/usr/bin/env python
"""
Script de test pour vérifier la connexion à l'API Orange Money WebPay Dev (sandbox).
Utilise les variables d'environnement définies dans .env
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

# Configuration Django minimale
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.conf import settings
import requests
import json

def test_orange_money_config():
    """Teste la configuration Orange Money."""
    print("=" * 60)
    print("TEST CONFIGURATION ORANGE MONEY")
    print("=" * 60)
    
    config = getattr(settings, 'ORANGE_MONEY', None)
    if not config:
        print("❌ Configuration Orange Money non trouvée dans settings")
        return False
    
    print("\n📋 Configuration détectée :")
    print(f"  - Environnement: {config.env}")
    print(f"  - Base URL: {config.base_url}")
    print(f"  - Merchant MSISDN: {'✅ Défini' if config.merchant_msisdn else '❌ Non défini'}")
    print(f"  - Merchant Code: {'✅ Défini' if config.merchant_code else '❌ Non défini'}")
    print(f"  - Login: {'✅ Défini' if config.login else '❌ Non défini'}")
    print(f"  - Password: {'✅ Défini' if config.password else '❌ Non défini'}")
    print(f"  - Test Subscriber MSISDN: {config.test_subscriber_msisdn}")
    print(f"  - Currency: {config.currency}")
    print(f"  - Country: {config.country}")
    
    # Vérifier les variables d'environnement directement
    print("\n🔍 Vérification des variables d'environnement :")
    env_vars = {
        'OM_ENV': os.getenv('OM_ENV'),
        'OM_BASE_URL': os.getenv('OM_BASE_URL'),
        'OM_MERCHANT_MSISDN': os.getenv('OM_MERCHANT_MSISDN'),
        'OM_MERCHANT_CODE': os.getenv('OM_MERCHANT_CODE'),
        'OM_LOGIN': os.getenv('OM_LOGIN'),
        'OM_PASSWORD': os.getenv('OM_PASSWORD'),
        'OM_MERCHANT_ID': os.getenv('OM_MERCHANT_ID'),
        'OM_MERCHANT_KEY': os.getenv('OM_MERCHANT_KEY'),
    }
    
    for key, value in env_vars.items():
        if value:
            # Masquer les valeurs sensibles
            if 'PASSWORD' in key or 'SECRET' in key or 'KEY' in key:
                display_value = f"{value[:3]}...{value[-3:]}" if len(value) > 6 else "***"
            else:
                display_value = value
            print(f"  ✅ {key}: {display_value}")
        else:
            print(f"  ❌ {key}: Non défini")
    
    return config


def test_api_connection(config):
    """Teste la connexion à l'API Orange Money."""
    print("\n" + "=" * 60)
    print("TEST CONNEXION API ORANGE MONEY")
    print("=" * 60)
    
    if not config.merchant_msisdn or not config.merchant_code:
        print("❌ Merchant MSISDN ou Code manquant - Impossible de tester l'API")
        return False
    
    if not config.login or not config.password:
        print("❌ Login ou Password manquant - Impossible de tester l'API")
        return False
    
    print(f"\n🔗 Test de connexion à: {config.base_url}")
    
    # Test 1: Vérifier que l'endpoint est accessible
    try:
        print("\n1️⃣ Test de base: Vérification de l'accessibilité de l'API...")
        response = requests.get(
            config.base_url,
            timeout=10,
            allow_redirects=True
        )
        print(f"   Status Code: {response.status_code}")
        if response.status_code in [200, 404, 405]:  # 404/405 signifie que l'API existe
            print("   ✅ L'endpoint est accessible")
        else:
            print(f"   ⚠️ Status inattendu: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False
    
    # Test 2: Essayer de créer une transaction de test
    print("\n2️⃣ Test de création de transaction (sandbox)...")
    
    import uuid
    test_reference = f"TEST-{uuid.uuid4().hex[:12].upper()}"
    
    # Construire le payload selon l'API Orange Money WebPay Dev
    payload = {
        "merchant_msisdn": config.merchant_msisdn,
        "merchant_code": config.merchant_code,
        "login": config.login,
        "password": config.password,
        "subscriber_msisdn": config.test_subscriber_msisdn,
        "amount": 100,  # Montant de test (1 FCFA)
        "currency": config.currency,
        "country": config.country,
        "reference": test_reference,
        "callback_url": config.callback_url,
        "return_success_url": config.return_success_url,
        "return_failure_url": config.return_failure_url,
    }
    
    print(f"   📤 Payload de test:")
    print(f"      - Reference: {test_reference}")
    print(f"      - Amount: {payload['amount']} {payload['currency']}")
    print(f"      - Subscriber: {payload['subscriber_msisdn']}")
    print(f"      - Merchant: {payload['merchant_msisdn']}")
    
    try:
        endpoint = f"{config.base_url}/webpayment"
        print(f"\n   🌐 Appel API: POST {endpoint}")
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
        )
        
        print(f"   📥 Status Code: {response.status_code}")
        print(f"   📥 Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"   📥 Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            print(f"   📥 Response Text: {response.text[:500]}")
        
        if response.status_code == 200:
            print("   ✅ Succès ! L'API a accepté la requête")
            return True
        elif response.status_code == 401:
            print("   ❌ Erreur d'authentification - Vérifiez vos credentials")
            return False
        elif response.status_code == 400:
            print("   ⚠️ Erreur de validation - Vérifiez le format du payload")
            return False
        else:
            print(f"   ⚠️ Réponse inattendue: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Timeout - L'API n'a pas répondu dans les délais")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur réseau: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Fonction principale de test."""
    print("\n" + "🚀" * 30)
    print("TEST API ORANGE MONEY SANDBOX")
    print("🚀" * 30 + "\n")
    
    # Test 1: Configuration
    config = test_orange_money_config()
    if not config:
        print("\n❌ Configuration non disponible - Arrêt du test")
        return
    
    # Test 2: Connexion API
    if config.merchant_msisdn and config.merchant_code and config.login and config.password:
        success = test_api_connection(config)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ TOUS LES TESTS SONT PASSÉS")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
            print("=" * 60)
            print("\n💡 Conseils:")
            print("   1. Vérifiez que toutes les variables sont correctes dans .env")
            print("   2. Vérifiez que l'URL de l'API est correcte")
            print("   3. Vérifiez que vos credentials Orange Money sont valides")
            print("   4. Consultez les logs ci-dessus pour plus de détails")
    else:
        print("\n⚠️ Credentials manquants - Impossible de tester l'API")
        print("   Veuillez renseigner dans .env:")
        print("   - OM_MERCHANT_MSISDN")
        print("   - OM_MERCHANT_CODE")
        print("   - OM_LOGIN")
        print("   - OM_PASSWORD")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == '__main__':
    main()
