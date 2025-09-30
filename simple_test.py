import hashlib
import hmac
import json

import requests

# Test simple avec la clé connue
secret = "1610448689"  # Début de CINETPAY_SECRET_KEY
payload = {"transaction_id": "TEST", "status": "SUCCESS"}
body = json.dumps(payload).encode("utf-8")
signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

print(f"Payload: {body.decode()}")
print(f"Secret: {secret}")
print(f"Signature: {signature}")

# Test avec curl
headers = {"Content-Type": "application/json", "X-Signature": signature}

try:
    response = requests.post(
        "http://127.0.0.1:8000/payments/cinetpay/notify/", data=body, headers=headers, timeout=5
    )
    print(f"Response: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Erreur: {e}")
