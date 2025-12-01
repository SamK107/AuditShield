#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple pour verifier la configuration CinetPay depuis .env
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
env_file = BASE_DIR / '.env'

print("\n" + "="*70)
print("DIAGNOSTIC CONFIGURATION CINETPAY")
print("="*70 + "\n")

# Lire le fichier .env directement
env_vars = {}
if env_file.exists():
    print(f"[OK] Fichier .env trouve: {env_file}\n")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                env_vars[key] = value
else:
    print(f"[WARN] Fichier .env non trouve a: {env_file}")
    print("Lecture des variables d'environnement systeme...\n")

# Vérifier les variables CinetPay
cinetpay_vars = {
    'CINETPAY_MOCK': env_vars.get('CINETPAY_MOCK', os.getenv('CINETPAY_MOCK', 'NON DEFINI')),
    'CINETPAY_API_KEY': env_vars.get('CINETPAY_API_KEY', os.getenv('CINETPAY_API_KEY', '')),
    'CINETPAY_SITE_ID': env_vars.get('CINETPAY_SITE_ID', os.getenv('CINETPAY_SITE_ID', '')),
    'CINETPAY_API_URL': env_vars.get('CINETPAY_API_URL', os.getenv('CINETPAY_API_URL', 'NON DEFINI')),
    'CINETPAY_RETURN_URL': env_vars.get('CINETPAY_RETURN_URL', os.getenv('CINETPAY_RETURN_URL', 'NON DEFINI')),
    'CINETPAY_NOTIFY_URL': env_vars.get('CINETPAY_NOTIFY_URL', os.getenv('CINETPAY_NOTIFY_URL', 'NON DEFINI')),
    'CINETPAY_ENV': env_vars.get('CINETPAY_ENV', os.getenv('CINETPAY_ENV', 'NON DEFINI')),
}

print("VARIABLES CINETPAY DETECTEES:")
print("-" * 70)
for key, value in cinetpay_vars.items():
    if key in ['CINETPAY_API_KEY', 'CINETPAY_SITE_ID']:
        if value:
            display = '*' * 12 + (value[-4:] if len(value) > 4 else '***')
        else:
            display = 'MANQUANT'
    else:
        display = value if value else 'NON DEFINI'
    
    status = "[OK]" if (key != 'CINETPAY_MOCK' and value and value != 'NON DEFINI') or (key == 'CINETPAY_MOCK' and value == '0') else "[ERREUR]"
    if key == 'CINETPAY_MOCK' and value == '1':
        status = "[ERREUR CRITIQUE]"
    print(f"{status} {key}: {display}")

# Analyse du problème
print("\n" + "="*70)
print("ANALYSE DU PROBLEME")
print("="*70 + "\n")

mock_value = cinetpay_vars.get('CINETPAY_MOCK', '0')
mock_enabled = str(mock_value).strip() == '1'

if mock_enabled:
    print("[ERREUR CRITIQUE] MODE MOCK ACTIVE!")
    print(f"   CINETPAY_MOCK = {mock_value}")
    print("\n   C'est la cause de votre probleme:")
    print("   1. Quand vous cliquez sur 'Payer avec CinetPay'")
    print("   2. Le systeme redirige vers /payments/cinetpay/mock/")
    print("   3. Cette page redirige IMMEDIATEMENT vers la page de retour")
    print("   4. Vous voyez la page de remerciement sans passer par CinetPay")
    print("\n   [SOLUTION] Dans votre fichier .env, changez:")
    print("      CINETPAY_MOCK=1")
    print("   en:")
    print("      CINETPAY_MOCK=0")
    print("   OU supprimez completement cette ligne")
else:
    print("[OK] Mode MOCK desactive")

# Vérifier les clés API
api_key = cinetpay_vars.get('CINETPAY_API_KEY', '')
site_id = cinetpay_vars.get('CINETPAY_SITE_ID', '')

print("\n" + "="*70)
print("VERIFICATION DES CLES API")
print("="*70 + "\n")

if not api_key:
    print("[ERREUR] CINETPAY_API_KEY est MANQUANTE")
    print("   Sans cette cle, le systeme ne peut pas appeler l'API CinetPay")
else:
    print("[OK] CINETPAY_API_KEY presente")

if not site_id:
    print("[ERREUR] CINETPAY_SITE_ID est MANQUANT")
    print("   Sans cet ID, le systeme ne peut pas appeler l'API CinetPay")
else:
    print("[OK] CINETPAY_SITE_ID present")

# Résumé
print("\n" + "="*70)
print("RESUME ET ACTIONS")
print("="*70 + "\n")

if mock_enabled:
    print("PROBLEME PRINCIPAL: Mode MOCK active")
    print("\nACTION IMMEDIATE REQUISE:")
    print("1. Ouvrez votre fichier .env")
    print("2. Trouvez la ligne: CINETPAY_MOCK=1")
    print("3. Changez-la en: CINETPAY_MOCK=0")
    print("   OU supprimez-la completement")
    print("4. Redemarrez votre serveur Django (Ctrl+C puis python manage.py runserver)")
elif not api_key or not site_id:
    print("PROBLEME: Cles API manquantes")
    print("\nACTION REQUISE:")
    print("1. Ajoutez dans votre .env:")
    print("   CINETPAY_API_KEY=votre_cle_api")
    print("   CINETPAY_SITE_ID=votre_site_id")
    print("2. Redemarrez votre serveur Django")
else:
    print("[OK] Configuration semble correcte")
    print("\nSi le probleme persiste:")
    print("1. Verifiez les logs Django (erreurs dans la console)")
    print("2. Verifiez que vos cles API sont valides")
    print("3. Verifiez que CINETPAY_ENV correspond a vos cles (sandbox/production)")

print("\n" + "="*70)

