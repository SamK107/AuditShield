# 📋 Configuration Orange Money - Résumé Technique

## 🎯 Configuration actuelle (Sandbox)

### Variables d'environnement (.env)

```bash
#=============================================================================
# ORANGE MONEY WEBPAY DEV - CONFIGURATION SANDBOX
#=============================================================================

# --- AUTHENTIFICATION OAUTH 2.0 ---
OM_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
OM_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
OM_OAUTH_URL=https://api.orange.com/oauth/v2/token

# --- IDENTITÉ MARCHAND ---
OM_MERCHANT_KEY=xxxxxxxx
OM_MERCHANT_MSISDN=7701900100              # (Optionnel)
OM_MERCHANT_ID=MerchantWP00100             # (Optionnel)
OM_AGENT_CODE=101021                       # (Optionnel)

# --- ENDPOINTS API SANDBOX ---
OM_WEBPAY_URL=https://api.orange.com/orange-money-webpay/dev/v1/webpayment
OM_TRANSACTION_STATUS_URL=https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus

# --- IDENTIFIANTS DE TEST (Sandbox) ---
OM_TEST_SUBSCRIBER_MSISDN=7701100100
OM_TEST_SUBSCRIBER_PIN=4940

# --- URLs DE RETOUR (Solution localhost) ---
OM_TEST_PUBLIC_URL=http://myvirtualshop.webnode.es
# OM_NGROK_URL=https://xxxx.ngrok.io        # Optionnel pour webhooks

# URLs de base (remplacées automatiquement si localhost détecté)
OM_RETURN_URL=http://127.0.0.1:8000/payments/om/return/
OM_NOTIFY_URL=http://127.0.0.1:8000/payments/om/notify/
OM_CANCEL_URL=http://127.0.0.1:8000/payments/om/return/

# --- MODE ---
OM_ENV=sandbox
```

---

## 📊 Payload API - Format utilisé

### 1. OAuth Request

```http
POST https://api.orange.com/oauth/v2/token
Authorization: Basic base64(OM_CLIENT_ID:OM_CLIENT_SECRET)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```

**Response** :
```json
{
  "access_token": "IW3gdUVOvQVcO7mGNsOZgwdhDNvE",
  "token_type": "Bearer",
  "expires_in": 7776000
}
```

---

### 2. WebPayment Request

```http
POST https://api.orange.com/orange-money-webpay/dev/v1/webpayment
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "merchant_key": "{OM_MERCHANT_KEY}",
  "currency": "OUV",
  "order_id": "{payment.uuid[:30]}",
  "amount": 15000,
  "return_url": "{OM_RETURN_URL}",
  "cancel_url": "{OM_RETURN_URL}",
  "notif_url": "{OM_NOTIFY_URL}",
  "lang": "fr",
  "reference": "AuditShield"
}
```

**Response attendue** :
```json
{
  "status": 201,
  "message": "OK",
  "pay_token": "f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a",
  "payment_url": "https://webpayment-qualif.orange-money.com/payment/pay_token/...",
  "notif_token": "dd497bda3b250e536186fc0663f32f40"
}
```

---

### 3. Webhook Notification

**Orange Money → Notre serveur** :
```http
POST {OM_NOTIFY_URL}
Content-Type: application/json

{
  "status": "SUCCESS",
  "notif_token": "dd497bda3b250e536186fc0663f32f40",
  "txnid": "MP150709.1341.A00073"
}
```

**Notre réponse** :
```json
{
  "status": "ok"
}
```

---

### 4. Transaction Status Request

```http
POST https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "merchant_key": "{OM_MERCHANT_KEY}",
  "order_id": "{order_id}",
  "amount": 15000,
  "pay_token": "f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a"
}
```

**Response** :
```json
{
  "status": "SUCCESS",
  "order_id": "abc-def-123",
  "txnid": "MP150709.1341.A00073"
}
```

---

## 🔄 Statuts de transaction

| Statut | Description | Durée de vie |
|--------|-------------|--------------|
| `INITIATED` | En attente d'entrée utilisateur | Jusqu'à 10 min |
| `PENDING` | Transaction en cours (user a cliqué "Confirmer") | Quelques secondes |
| `EXPIRED` | Token expiré (user a pris >10 min) | Final |
| `SUCCESS` | ✅ Paiement réussi | Final |
| `FAILED` | ❌ Paiement échoué | Final |

---

## 🔐 Sécurité et validation

### Token validation (webhook)

```python
# 1. Stocker notif_token lors de la création du paiement
payment.notif_token = response["notif_token"]

# 2. Vérifier notif_token lors de la réception du webhook
if webhook_payload["notif_token"] != payment.notif_token:
    return {"error": "Invalid notif_token"}
```

### Idempotence

```python
# Vérifier si le paiement a déjà été traité
if order.status == "PAID":
    logger.info("Order déjà payé, ignorer webhook")
    return {"status": "ok"}
```

---

## 🛠️ Spécificités implémentées

### 1. Cache du token OAuth

```python
# Cache Django : durée de vie ~90 jours
_TOKEN_CACHE_KEY = "orange_money_access_token"
_TOKEN_CACHE_TIMEOUT = 90 * 24 * 60 * 60  # 90 jours

# Expiration anticipée de 1h pour sécurité
cache_timeout = min(expires_in - 3600, _TOKEN_CACHE_TIMEOUT)
```

### 2. Gestion des URLs localhost

```python
# Détection automatique de localhost
has_localhost = ("localhost" in return_url.lower() or 
                 "127.0.0.1" in return_url.lower())

if has_localhost:
    # Option A : URL publique de test (sandbox)
    if OM_TEST_PUBLIC_URL:
        return_url = OM_TEST_PUBLIC_URL + reverse("store:orange_return")
    
    # Option B : ngrok (pour webhooks en local)
    if OM_NGROK_URL:
        notify_url = OM_NGROK_URL + reverse("store:orange_notify")
    
    # Fallback : URL de test par défaut
    else:
        return_url = "http://myvirtualshop.webnode.es/payments/om/return/"
```

### 3. Reconstruction URL sandbox

```python
# Mode sandbox : utiliser le domaine sandbox correct
if "/dev/v1/webpayment" in webpay_url:
    sandbox_payment_url = (
        f"https://webpayment-ow-sb.orange-money.com/"
        f"payment/pay_token/{pay_token}"
    )
    payment_url = sandbox_payment_url
else:
    # Mode production : utiliser l'URL retournée par l'API
    payment_url = response["payment_url"]
```

---

## 📂 Architecture des fichiers

```
auditshield/
├── store/
│   ├── services/
│   │   └── orange_money.py                    # ✅ Service principal
│   │       ├── get_access_token()             # OAuth 2.0
│   │       ├── create_payment_request()       # Création paiement
│   │       ├── check_transaction_status()     # Vérification statut
│   │       ├── verify_webhook()               # Validation webhook
│   │       └── map_provider_status_to_paid()  # Mapping statuts
│   │
│   ├── payment_views.py                       # Vues Django
│   │   ├── orange_start_payment()             # Initiation paiement
│   │   ├── orange_return()                    # Retour utilisateur
│   │   └── orange_notify()                    # Webhook notification
│   │
│   ├── urls.py                                # Configuration URLs
│   │   ├── /buy/om/<slug>/                    # → orange_start_payment
│   │   ├── /payments/om/return/               # → orange_return
│   │   └── /payments/om/notify/               # → orange_notify
│   │
│   └── templates/store/
│       └── payment_pending.html               # Page "en cours"
│
├── docs/
│   ├── orange_money_sandbox.md                # Guide de test
│   ├── PRESENTATION_ORANGE_MONEY_POUR_AGENTS.md    # Doc complète
│   └── PRESENTATION_RAPIDE_ORANGE_AGENTS.md   # Présentation rapide
│
├── guide_orange.md                            # Guide officiel Orange
├── ENV_TEMPLATE.txt                           # Template .env
└── .env                                       # Variables (Git ignored)
```

---

## 🧪 Commandes de test

### Créer un paiement de test

```bash
python manage.py test_orange_money_sandbox --amount 100
```

**Output attendu** :
```
=== Test Orange Money Sandbox (montant: 100 FCFA) ===

✓ Configuration chargée
✓ Order créé: 123 (uuid: abc-def-...)
✓ Paiement créé avec succès

Order ID: abc-def-123
Pay Token: f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a
Payment URL: https://webpayment-ow-sb.orange-money.com/payment/pay_token/...
```

### Vérifier le statut d'une transaction

```bash
python manage.py test_orange_money_sandbox \
  --check-status abc-def-123 \
  --pay-token f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a
```

**Output attendu** :
```
=== Vérification du statut ===
Order ID: abc-def-123
Status: SUCCESS
Transaction ID: MP150709.1341.A00073
```

### Vider le cache OAuth

```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.delete('orange_money_access_token')
>>> exit()
```

---

## 📊 Diagramme de séquence

```
User                Django              Orange API          OTP Simulator
 │                    │                     │                     │
 │  1. Acheter        │                     │                     │
 ├───────────────────>│                     │                     │
 │                    │  2. OAuth Token     │                     │
 │                    ├────────────────────>│                     │
 │                    │<────────────────────┤                     │
 │                    │  access_token       │                     │
 │                    │                     │                     │
 │                    │  3. Create Payment  │                     │
 │                    ├────────────────────>│                     │
 │                    │<────────────────────┤                     │
 │                    │  pay_token,         │                     │
 │                    │  payment_url,       │                     │
 │                    │  notif_token        │                     │
 │                    │                     │                     │
 │  4. Redirect       │                     │                     │
 │<───────────────────┤                     │                     │
 │  to payment_url    │                     │                     │
 │                    │                     │                     │
 │  5. Enter MSISDN + OTP                   │                     │
 ├──────────────────────────────────────────>│                     │
 │                    │                     │  6. Generate OTP    │
 │                    │                     │<────────────────────┤
 │                    │                     │                     │
 │  7. Confirm        │                     │                     │
 ├──────────────────────────────────────────>│                     │
 │                    │                     │                     │
 │                    │  8. Webhook Notify  │                     │
 │                    │<────────────────────┤                     │
 │                    │  {status: SUCCESS}  │                     │
 │                    │                     │                     │
 │                    │  9. Mark PAID       │                     │
 │                    │     Send Email      │                     │
 │                    │                     │                     │
 │  10. Redirect      │                     │                     │
 │<───────────────────┤                     │                     │
 │  to return_url     │                     │                     │
```

---

## 🔍 Logs détaillés

### Activation des logs DEBUG

```python
# Dans config/settings/dev.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'store.services.orange_money': {
            'handlers': ['console'],
            'level': 'DEBUG',  # ← DEBUG pour tout voir
            'propagate': False,
        },
    },
}
```

### Exemples de logs

```
INFO [OM][OAuth] Requesting token from https://api.orange.com/oauth/v2/token
INFO [OM][OAuth] Token obtenu avec succès (cache pour 7776000s)

INFO [OM][create_payment] Initiating payment: order_id=abc-def-123, amount=15000 XOF
DEBUG [OM][create_payment] Payload: {
  "merchant_key": "xxxxxxxx",
  "currency": "OUV",
  "order_id": "abc-def-123",
  "amount": 15000,
  "return_url": "http://myvirtualshop.webnode.es/payments/om/return/",
  ...
}
INFO [OM][create_payment] Response status=201 | status=201 | message=OK
INFO [OM][create_payment] Payment créé avec succès | payment_url=https://... | pay_token=f5720dd...

INFO [OM][verify_webhook] Payload reçu | status=SUCCESS | notif_token=dd497b... | txnid=MP150709...
DEBUG [OM][verify_webhook] Full payload: {
  "status": "SUCCESS",
  "notif_token": "dd497bda3b250e536186fc0663f32f40",
  "txnid": "MP150709.1341.A00073"
}
```

---

## ⚠️ Troubleshooting

### Erreur : 401 Unauthorized (OAuth)

**Cause** : `OM_CLIENT_ID` ou `OM_CLIENT_SECRET` incorrect

**Solution** :
1. Vérifier sur https://developer.orange.com/myapps
2. Régénérer les credentials si nécessaire
3. Vider le cache : `cache.delete('orange_money_access_token')`

---

### Erreur : 403 Forbidden (WebPay)

**Cause** : `OM_MERCHANT_KEY` incorrecte ou URLs localhost

**Solution** :
1. Vérifier Merchant Key sur Orange Developer Portal
2. Configurer `OM_TEST_PUBLIC_URL` ou `OM_NGROK_URL`
3. Vérifier que la devise est `OUV` en sandbox

---

### Erreur : Webhook non reçu

**Cause** : `notif_url` n'est pas accessible publiquement

**Solution** :
1. Utiliser ngrok : `ngrok http 8000`
2. Configurer `OM_NGROK_URL=https://xxxx.ngrok.io`
3. Vérifier que la transaction a été validée (statut `SUCCESS`)

---

### Erreur : Payment URL timeout

**Cause** : `pay_token` expiré (>10 minutes)

**Solution** :
1. Créer une nouvelle transaction
2. Valider dans les 10 minutes

---

## 📞 Support

| Ressource | Contact/Lien |
|-----------|--------------|
| **Simulateur OTP** | https://mpayment.orange-money.com/mpayment-otp/login |
| **Developer Portal** | https://developer.orange.com/myapps |
| **Support Orange** | georgiana.cruceru@orange.com |
| **Documentation** | `guide_orange.md`, `docs/orange_money_sandbox.md` |

---

## ✅ Checklist de validation

### Configuration

- [x] `OM_CLIENT_ID` configuré
- [x] `OM_CLIENT_SECRET` configuré
- [x] `OM_MERCHANT_KEY` configuré
- [x] `OM_OAUTH_URL` configuré (v2/token)
- [x] `OM_WEBPAY_URL` configuré (/dev/v1/webpayment)
- [x] `OM_TRANSACTION_STATUS_URL` configuré
- [x] `OM_TEST_PUBLIC_URL` configuré (fallback localhost)

### Implémentation

- [x] OAuth 2.0 avec cache
- [x] Création de paiement WebPay
- [x] Webhook de notification
- [x] Vérification de statut
- [x] Gestion localhost automatique
- [x] Logging complet

### Tests

- [x] Commande `test_orange_money_sandbox` créée
- [x] Test OAuth réussi
- [x] Test création paiement réussi
- [ ] Test E2E avec Simulateur OTP (en attente identifiants)
- [ ] Test webhook (en attente identifiants)

---

**Document technique** pour agents Orange Money  
**Date** : 4 décembre 2024  
**Version** : 1.0.0 (Sandbox)

