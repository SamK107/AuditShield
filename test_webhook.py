#!/usr/bin/env python3
import hashlib
import hmac
import json
import os

import requests

# Configuration
WEBHOOK_URL = "http://127.0.0.1:8000/payments/cinetpay/notify/"
ORDER_ID = "7583FE078C994F16B7DC999A"  # Dernière commande

# Payload de test
payload = {"transaction_id": ORDER_ID, "status": "SUCCESS", "amount": 100, "currency": "XOF"}

# Convertir en JSON
body = json.dumps(payload).encode("utf-8")

# Signature HMAC (utilise CINETPAY_SECRET_KEY en priorité comme notre code Django)
secret_key = os.environ.get("CINETPAY_SECRET_KEY") or os.environ.get("CINETPAY_API_KEY") or ""
print(f"🔑 Clé utilisée (10 premiers chars): {secret_key[:10]}...")
signature = hmac.new(secret_key.encode("utf-8"), body, hashlib.sha256).hexdigest()

# Headers
headers = {"Content-Type": "application/json", "X-Signature": signature}

print(f"🧪 Test webhook CinetPay")
print(f"URL: {WEBHOOK_URL}")
print(f"Order ID: {ORDER_ID}")
print(f"Signature: {signature[:20]}...")

# Envoyer la requête
try:
    response = requests.post(WEBHOOK_URL, data=body, headers=headers, timeout=10)
    print(f"✅ Statut: {response.status_code}")
    print(f"✅ Réponse: {response.text}")
except Exception as e:
    print(f"❌ Erreur: {e}")
