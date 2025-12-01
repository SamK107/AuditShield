#!/usr/bin/env python
"""
Script de diagnostic pour verifier la configuration CinetPay
"""
import os
import sys
import django
from pathlib import Path

# Ajouter le chemin du projet
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[OK] Fichier .env charge depuis: {env_path}")
    else:
        print(f"[WARN] Fichier .env non trouve a: {env_path}")
except ImportError:
    print("[WARN] python-dotenv non installe, lecture directe des variables d'environnement")
except Exception as e:
    print(f"[WARN] Erreur lors du chargement .env: {e}")

print("\n" + "="*60)
print("DIAGNOSTIC CONFIGURATION CINETPAY")
print("="*60 + "\n")

# Vérifier les variables d'environnement
print("Variables d'environnement (.env):")
print("-" * 60)

env_vars = {
    "CINETPAY_MOCK": os.getenv("CINETPAY_MOCK", "NON DÉFINI"),
    "CINETPAY_API_KEY": "PRÉSENTE" if os.getenv("CINETPAY_API_KEY") else "MANQUANTE",
    "CINETPAY_SITE_ID": "PRÉSENT" if os.getenv("CINETPAY_SITE_ID") else "MANQUANT",
    "CINETPAY_API_URL": os.getenv("CINETPAY_API_URL", "NON DÉFINI"),
    "CINETPAY_RETURN_URL": os.getenv("CINETPAY_RETURN_URL", "NON DÉFINI"),
    "CINETPAY_NOTIFY_URL": os.getenv("CINETPAY_NOTIFY_URL", "NON DÉFINI"),
    "CINETPAY_ENV": os.getenv("CINETPAY_ENV", "NON DÉFINI"),
}

for key, value in env_vars.items():
    status = "[OK]" if value not in ["NON DÉFINI", "MANQUANTE", "MANQUANT"] else "[ERREUR]"
    print(f"{status} {key}: {value}")

# Vérifier le mode mock
print("\n" + "="*60)
print("ANALYSE DU MODE MOCK")
print("="*60 + "\n")

mock_env = os.getenv("CINETPAY_MOCK", "0")
mock_enabled = mock_env == "1"

if mock_enabled:
    print("[ERREUR] PROBLEME DETECTE: Mode MOCK active!")
    print(f"   CINETPAY_MOCK={mock_env}")
    print("\n   [WARN] Le mode MOCK fait que:")
    print("   1. Vous etes redirige vers /payments/cinetpay/mock/")
    print("   2. Cette page redirige immediatement vers la page de retour")
    print("   3. Le checkout CinetPay est contourne")
    print("\n   [SOLUTION] Mettez CINETPAY_MOCK=0 dans votre .env")
else:
    print("[OK] Mode MOCK desactive (CINETPAY_MOCK=0 ou non defini)")

# Vérifier les clés API
print("\n" + "="*60)
print("VERIFICATION DES CLES API")
print("="*60 + "\n")

api_key = os.getenv("CINETPAY_API_KEY")
site_id = os.getenv("CINETPAY_SITE_ID")

if not api_key or not site_id:
    print("[ERREUR] PROBLEME: Cles API manquantes!")
    if not api_key:
        print("   - CINETPAY_API_KEY est manquante")
    if not site_id:
        print("   - CINETPAY_SITE_ID est manquant")
    print("\n   [WARN] Sans ces cles, le systeme peut:")
    print("   1. Lever une exception")
    print("   2. Utiliser le mode mock par defaut")
    print("\n   [SOLUTION] Ajoutez vos cles CinetPay dans le .env")
else:
    print("[OK] Cles API presentes")
    if api_key:
        print(f"   - CINETPAY_API_KEY: {'*' * 8}{api_key[-4:] if len(api_key) > 4 else '***'}")
    if site_id:
        print(f"   - CINETPAY_SITE_ID: {'*' * 8}{site_id[-4:] if len(site_id) > 4 else '***'}")

# Vérifier les URLs
print("\n" + "="*60)
print("VERIFICATION DES URLs")
print("="*60 + "\n")

return_url = os.getenv("CINETPAY_RETURN_URL")
notify_url = os.getenv("CINETPAY_NOTIFY_URL")

if return_url:
    print(f"[OK] CINETPAY_RETURN_URL: {return_url}")
else:
    print("[WARN] CINETPAY_RETURN_URL non defini (fallback dynamique sera utilise)")

if notify_url:
    print(f"[OK] CINETPAY_NOTIFY_URL: {notify_url}")
else:
    print("[WARN] CINETPAY_NOTIFY_URL non defini (fallback dynamique sera utilise)")

# Résumé et recommandations
print("\n" + "="*60)
print("RESUME ET RECOMMANDATIONS")
print("="*60 + "\n")

issues = []
if mock_enabled:
    issues.append("Mode MOCK active (CINETPAY_MOCK=1)")
if not api_key:
    issues.append("CINETPAY_API_KEY manquante")
if not site_id:
    issues.append("CINETPAY_SITE_ID manquant")

if issues:
    print("[ERREUR] PROBLEMES DETECTES:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    
    print("\n[SOLUTION] ACTIONS A PRENDRE:")
    print("\n   1. Ouvrez votre fichier .env")
    print("   2. Assurez-vous que:")
    print("      - CINETPAY_MOCK=0 (ou supprimez cette ligne)")
    print("      - CINETPAY_API_KEY=votre_vraie_cle_api")
    print("      - CINETPAY_SITE_ID=votre_vrai_site_id")
    print("   3. Redemarrez votre serveur Django")
else:
    print("[OK] Configuration semble correcte pour le mode PRODUCTION")
    print("\n   Si vous etes toujours redirige vers la page de remerciement:")
    print("   1. Verifiez les logs Django pour les erreurs")
    print("   2. Verifiez que l'API CinetPay repond correctement")
    print("   3. Verifiez que vous utilisez les bonnes cles (sandbox vs production)")

print("\n" + "="*60)

