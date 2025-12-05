# 🎯 Intégration Orange Money WebPay - Présentation Rapide
## AuditShield - Mode Sandbox

---

## 📌 Vue d'ensemble en 30 secondes

**Projet** : AuditShield (plateforme d'audit comptable au Mali)  
**Intégration** : Orange Money WebPay Dev (API Sandbox)  
**Objectif** : Paiement d'ebooks et kits d'audit professionnels  
**Statut** : ✅ Implémenté et testé (en attente identifiants de test complets)

---

## 🔧 Configuration technique

### Endpoints utilisés

| API | URL |
|-----|-----|
| **OAuth** | `https://api.orange.com/oauth/v2/token` |
| **WebPay** | `https://api.orange.com/orange-money-webpay/dev/v1/webpayment` |
| **Status** | `https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus` |
| **Payment Page** | `https://webpayment-ow-sb.orange-money.com/payment/pay_token/{token}` |

### Variables configurées

```bash
✅ OM_CLIENT_ID          # OAuth Client ID
✅ OM_CLIENT_SECRET      # OAuth Secret
✅ OM_MERCHANT_KEY       # Merchant Key (généré sur Orange Portal)
✅ OM_OAUTH_URL          # OAuth endpoint
✅ OM_WEBPAY_URL         # WebPay endpoint (/dev/v1/)
✅ OM_RETURN_URL         # URL de retour utilisateur
✅ OM_NOTIFY_URL         # URL webhook notification
```

---

## 🔄 Flux de paiement

```
┌─────────────┐
│ Utilisateur │
│   achète    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ 1. OAuth Token      │  POST /oauth/v2/token
│    (Django cache)   │  → access_token
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ 2. Create Payment   │  POST /webpayment
│    (order_id, amt)  │  → pay_token, payment_url
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ 3. Redirect         │  https://webpayment-ow-sb.orange-money.com/
│    → Orange Page    │  payment/pay_token/{token}
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ 4. User enters      │  MSISDN + OTP
│    credentials      │  (via Simulateur OTP)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ 5. Webhook          │  POST /payments/om/notify/
│    (notif_token)    │  → status: SUCCESS
│    → Mark PAID      │  → Send email
└─────────────────────┘
```

---

## 📊 Paramètres clés du payload

### Request `/webpayment`

```json
{
  "merchant_key": "xxxxxxxx",
  "currency": "OUV",              // ⚠️ OUV en sandbox, XOF en prod
  "order_id": "uuid-30-chars",    // Unique, max 30 chars
  "amount": 15000,                // FCFA (entier)
  "return_url": "...",            // URL retour utilisateur
  "cancel_url": "...",            // URL annulation
  "notif_url": "...",             // ⚠️ Webhook (PAS localhost)
  "lang": "fr",
  "reference": "AuditShield"      // Max 30 chars
}
```

### Response

```json
{
  "status": 201,                  // ⚠️ 201 (pas 200)
  "message": "OK",
  "pay_token": "f5720dd...",
  "payment_url": "https://...",
  "notif_token": "dd497bd..."     // ⚠️ À stocker et vérifier
}
```

### Webhook received

```json
{
  "status": "SUCCESS",            // SUCCESS / FAILED
  "notif_token": "dd497bd...",    // ⚠️ Doit correspondre
  "txnid": "MP150709.1341.A00073"
}
```

---

## ⚙️ Spécificités de l'implémentation

### 1. ✅ Cache du token OAuth
- Token mis en cache Django pendant ~90 jours
- Réutilisé automatiquement jusqu'à expiration
- Expiration anticipée de 1h pour éviter les erreurs

### 2. ✅ Gestion des URLs localhost
**Problème** : Orange Money refuse `localhost` ou `127.0.0.1`

**Solution implémentée** :
```python
# Le code détecte automatiquement localhost et utilise :

# Option A : URL de test publique (sandbox)
OM_TEST_PUBLIC_URL = "http://myvirtualshop.webnode.es"

# Option B : ngrok (pour recevoir webhooks en local)
OM_NGROK_URL = "https://xxxx.ngrok.io"
```

### 3. ✅ Reconstruction de l'URL sandbox
```python
# L'API retourne parfois une URL qualif
# Le code reconstruit l'URL sandbox correcte :
payment_url = f"https://webpayment-ow-sb.orange-money.com/payment/pay_token/{pay_token}"
```

### 4. ✅ Validation webhook via `notif_token`
```python
# Stocké lors de la création du paiement
# Vérifié lors de la réception du webhook
# = Seule source de validation (pas de HMAC)
```

---

## 🧪 Tests disponibles

### Commande de test

```bash
# Créer un paiement de test
python manage.py test_orange_money_sandbox --amount 100

# Output attendu :
# ✓ Order créé
# ✓ Token OAuth obtenu
# ✓ Paiement créé
# → Payment URL : https://webpayment-ow-sb.orange-money.com/payment/pay_token/...
```

### Vérification de statut

```bash
python manage.py test_orange_money_sandbox \
  --check-status ORDER_ID \
  --pay-token PAY_TOKEN

# Output attendu :
# → Status: SUCCESS / INITIATED / PENDING / EXPIRED / FAILED
```

---

## 🔍 Logging

### Format standardisé
```
[OM][fonction] Message | key1=value1 | key2=value2
```

### Exemples
```
[OM][OAuth] Token obtenu avec succès (cache pour 7776000s)
[OM][create_payment] Initiating payment: order_id=abc, amount=15000 XOF
[OM][create_payment] Payment créé avec succès | payment_url=https://...
[OM][verify_webhook] Payload reçu | status=SUCCESS | txnid=MP150709...
```

---

## ⚠️ Points d'attention

### 1. Erreur OAuth (401/403)
**Cause** : `OM_CLIENT_ID` ou `OM_CLIENT_SECRET` incorrect  
**Solution** : Vérifier sur Orange Developer Portal

### 2. Erreur WebPay (400/401/403)
**Cause** : `OM_MERCHANT_KEY` incorrecte ou URLs localhost  
**Solution** : Vérifier Merchant Key + configurer `OM_TEST_PUBLIC_URL`

### 3. Webhook non reçu
**Cause** : `notif_url` n'est pas accessible publiquement  
**Solution** : Utiliser `ngrok` ou attendre déploiement production

### 4. Payment URL timeout
**Cause** : `pay_token` expiré (>10 min) ou URL incorrecte  
**Solution** : Créer une nouvelle transaction

---

## 📋 Checklist pour les agents Orange

### Vérifications à faire

- [ ] **Credentials OAuth** : `OM_CLIENT_ID` et `OM_CLIENT_SECRET` sont corrects ?
- [ ] **Merchant Key** : `OM_MERCHANT_KEY` générée correctement ?
- [ ] **Endpoints** : URLs API sandbox correctes (`/dev/v1/`) ?
- [ ] **Currency** : `OUV` bien utilisée en sandbox ?
- [ ] **Status code** : Réponse `201` (pas `200`) bien attendue ?
- [ ] **notif_token** : Présent dans la réponse WebPay ?
- [ ] **payment_url** : URL sandbox correcte retournée ?

### Tests à effectuer

- [ ] **OAuth** : Token obtenu avec succès ?
- [ ] **WebPay** : `pay_token` et `payment_url` retournés ?
- [ ] **Payment Page** : URL sandbox se charge correctement ?
- [ ] **OTP Simulator** : Accès et génération d'OTP fonctionnels ?
- [ ] **Webhook** : Notification reçue après validation ?
- [ ] **Status API** : Vérification de statut fonctionnelle ?

---

## 🎯 Ce qu'on attend de vous

### Identifiants de test nécessaires

**Channel User (Merchant)** :
```
✅ Login/ID           : MerchantWP00100 (exemple)
✅ Account Number     : 7701900100 (exemple)
✅ Merchant Code      : 101021 (exemple)
✅ PIN code           : xxxx (à fournir)
```

**Subscriber (Client)** :
```
✅ MSISDN             : 7701100100 (exemple)
✅ PIN                : xxxx (à fournir)
```

### Support requis

1. ✅ Validation de notre configuration actuelle
2. ✅ Test E2E avec Simulateur OTP
3. ✅ Vérification du format webhook (réponse réelle)
4. ✅ Assistance si erreurs API rencontrées

---

## 📞 Contacts

| Ressource | Lien/Contact |
|-----------|--------------|
| **Simulateur OTP** | https://mpayment.orange-money.com/mpayment-otp/login |
| **Developer Portal** | https://developer.orange.com/myapps |
| **Support Orange** | georgiana.cruceru@orange.com |

---

## 📝 Résumé

| ✅ Fait | ⏳ En attente |
|---------|---------------|
| Service API complet | Identifiants de test complets |
| OAuth 2.0 + cache | Test E2E avec Simulateur OTP |
| Création paiement | Validation format webhook réel |
| Webhook notification | Identifiants production |
| Vérification statut | |
| Gestion localhost | |
| Logging complet | |
| Commandes de test | |

---

**Document préparé pour** : Agents Orange Money  
**Date** : 4 décembre 2024  
**Contact** : AuditShield Dev Team

