# 🚀 Orange Money - Référence Rapide

## Configuration Sandbox AuditShield

---

## 🔧 Variables essentielles (.env)

```bash
# OAuth
OM_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
OM_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
OM_OAUTH_URL=https://api.orange.com/oauth/v2/token

# Merchant
OM_MERCHANT_KEY=xxxxxxxx

# Endpoints Sandbox
OM_WEBPAY_URL=https://api.orange.com/orange-money-webpay/dev/v1/webpayment
OM_TRANSACTION_STATUS_URL=https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus

# URLs (localhost → URL de test automatique)
OM_TEST_PUBLIC_URL=http://myvirtualshop.webnode.es
OM_RETURN_URL=http://127.0.0.1:8000/payments/om/return/
OM_NOTIFY_URL=http://127.0.0.1:8000/payments/om/notify/
```

---

## 📊 Payloads clés

### OAuth
```http
POST /oauth/v2/token
Authorization: Basic base64(CLIENT_ID:CLIENT_SECRET)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```

### WebPayment
```json
POST /orange-money-webpay/dev/v1/webpayment
{
  "merchant_key": "xxxxxxxx",
  "currency": "OUV",              // ⚠️ OUV (sandbox) / XOF (prod)
  "order_id": "unique-30-chars",
  "amount": 15000,
  "return_url": "...",
  "cancel_url": "...",
  "notif_url": "...",             // ⚠️ PAS localhost
  "lang": "fr",
  "reference": "AuditShield"
}

Response: 201 ✓ (pas 200)
{
  "pay_token": "f5720dd...",
  "payment_url": "https://...",
  "notif_token": "dd497bd..."     // ⚠️ À stocker et vérifier
}
```

### Webhook
```json
POST {notif_url}
{
  "status": "SUCCESS",            // SUCCESS / FAILED
  "notif_token": "dd497bd...",    // ⚠️ Doit correspondre
  "txnid": "MP150709.1341.A00073"
}
```

---

## 🔄 Flux

```
1. OAuth        → access_token (cache 90j)
2. WebPayment   → pay_token, payment_url, notif_token
3. Redirect     → Orange Money page
4. User         → Enter MSISDN + OTP (Simulator)
5. Webhook      → Validate notif_token → Mark PAID
6. Return       → Show "En cours" (NOT validate)
```

---

## 🎯 Statuts

| Code | Description | Final? |
|------|-------------|--------|
| `INITIATED` | En attente | ❌ |
| `PENDING` | En cours | ❌ |
| `EXPIRED` | Expiré (>10min) | ✅ |
| `SUCCESS` | ✅ Payé | ✅ |
| `FAILED` | ❌ Échoué | ✅ |

---

## ⚠️ Points critiques

### Sandbox vs Production

| Paramètre | Sandbox | Production |
|-----------|---------|------------|
| **Endpoint** | `/dev/v1/webpayment` | `/v1/webpayment` |
| **Currency** | `OUV` | `XOF` |
| **Payment URL** | `webpayment-ow-sb.orange-money.com` | `webpayment.orange-money.com` |
| **OAuth** | Identique | Identique |

### URLs localhost

**Problème** : Orange refuse `localhost` / `127.0.0.1`

**Solution auto** :
```python
# Détecte localhost → remplace par OM_TEST_PUBLIC_URL
# Pour webhooks locaux → utiliser OM_NGROK_URL
```

### Validation webhook

```python
# ⚠️ CRITIQUE : Vérifier notif_token
if webhook["notif_token"] != stored_notif_token:
    return 403
```

---

## 🧪 Tests

```bash
# Créer paiement test
python manage.py test_orange_money_sandbox --amount 100

# Vérifier statut
python manage.py test_orange_money_sandbox \
  --check-status ORDER_ID --pay-token TOKEN

# Vider cache OAuth
python manage.py shell
>>> from django.core.cache import cache
>>> cache.delete('orange_money_access_token')
```

---

## 🐛 Erreurs courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| `401 OAuth` | CLIENT_ID/SECRET incorrect | Vérifier sur Portal |
| `403 WebPay` | MERCHANT_KEY incorrect | Vérifier Merchant Key |
| `403 WebPay` | URLs localhost | Configurer TEST_PUBLIC_URL |
| Webhook ❌ | notif_url inaccessible | Utiliser ngrok |
| Payment timeout | pay_token expiré (>10min) | Nouvelle transaction |

---

## 📞 Ressources

| Ressource | Lien |
|-----------|------|
| **Simulator OTP** | https://mpayment.orange-money.com/mpayment-otp/login |
| **Dev Portal** | https://developer.orange.com/myapps |
| **Support** | georgiana.cruceru@orange.com |

**Login Simulator** :
- Login: Merchant Account Number (`7701900100`)
- Password: Channel User ID (`MerchantWP00100`)

---

## 📂 Fichiers clés

```
store/services/orange_money.py      # Service principal
store/payment_views.py              # Vues Django
store/urls.py                       # Routes
docs/orange_money_sandbox.md        # Guide complet
guide_orange.md                     # Guide officiel Orange
```

---

## 🎯 Checklist

### Config
- [x] CLIENT_ID + CLIENT_SECRET
- [x] MERCHANT_KEY
- [x] Endpoints `/dev/v1/`
- [x] TEST_PUBLIC_URL (localhost)

### Code
- [x] OAuth + cache
- [x] WebPayment
- [x] Webhook validation
- [x] Status check
- [x] Logging

### Tests
- [x] OAuth ✓
- [x] WebPayment ✓
- [ ] E2E OTP
- [ ] Webhook
- [ ] Status

---

**Quick Ref** - Orange Money Sandbox  
**Date** : 4 déc 2024

