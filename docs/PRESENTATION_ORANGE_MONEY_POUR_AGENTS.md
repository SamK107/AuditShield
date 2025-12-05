# 📋 Présentation de l'intégration Orange Money WebPay Dev - AuditShield

## 🎯 Objectif de ce document

Ce document présente l'**implémentation complète** de l'API Orange Money WebPay Dev (mode **Sandbox**) dans le projet **AuditShield**. Il est destiné aux **agents Orange Money** pour faciliter le support technique et la compréhension de notre intégration.

---

## 📱 Contexte du projet AuditShield

**AuditShield** est une plateforme d'audit comptable au Mali qui vend :
1. **Ebooks** : "Audit Sans Peur" et autres ressources
2. **Kits complets** : Kits d'audit personnalisés (documents professionnels)

**Mode de paiement** : CinetPay (principal) + **Orange Money** (en intégration)

---

## 🏗️ Architecture de l'intégration Orange Money

### 1. Structure des fichiers

```
auditshield/
├── store/
│   ├── services/
│   │   └── orange_money.py          # ✅ Service API Orange Money (code principal)
│   ├── payment_views.py              # Vues de paiement (routes Django)
│   ├── urls.py                       # Configuration des URLs
│   └── templates/store/
│       └── payment_pending.html      # Page "paiement en cours"
├── docs/
│   └── orange_money_sandbox.md       # Guide de test sandbox
├── guide_orange.md                    # Guide officiel Orange (PDF converti)
├── ENV_TEMPLATE.txt                   # Template des variables d'environnement
└── .env                              # Variables d'environnement (ignoré par Git)
```

---

## ⚙️ Configuration actuelle (Mode Sandbox)

### Variables d'environnement dans `.env`

```bash
# ============================================
# ORANGE MONEY WEBPAY DEV (Mali, Sandbox)
# ============================================

# --- 1. AUTHENTIFICATION OAUTH 2.0 ---
OM_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
OM_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
OM_OAUTH_URL=https://api.orange.com/oauth/v2/token

# --- 2. IDENTITÉ MARCHAND ---
OM_MERCHANT_KEY=xxxxxxxx                    # Clé générée sur Orange Developer Portal
OM_MERCHANT_MSISDN=7701900100              # (Optionnel) Merchant Account Number
OM_MERCHANT_ID=MerchantWP00100             # (Optionnel) Channel User ID
OM_AGENT_CODE=101021                       # (Optionnel) Merchant Code

# --- 3. ENDPOINTS API SANDBOX ---
OM_WEBPAY_URL=https://api.orange.com/orange-money-webpay/dev/v1/webpayment
OM_TRANSACTION_STATUS_URL=https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus

# --- 4. IDENTIFIANTS DE TEST (Subscriber Sandbox) ---
OM_TEST_SUBSCRIBER_MSISDN=7701100100       # Numéro de test fourni par Orange
OM_TEST_SUBSCRIBER_PIN=4940                # PIN de test fourni par Orange

# --- 5. URLs DE RETOUR ET WEBHOOK ---
# ⚠️ IMPORTANT: Orange Money n'accepte PAS localhost/127.0.0.1
# Pour le développement local, utiliser une URL publique de test ou ngrok

# Option A: URL publique de test (pour sandbox uniquement)
OM_TEST_PUBLIC_URL=http://myvirtualshop.webnode.es

# Option B: ngrok (pour recevoir les webhooks en local)
# OM_NGROK_URL=https://xxxx.ngrok.io

# URLs par défaut (remplacées automatiquement si localhost détecté)
OM_RETURN_URL=http://127.0.0.1:8000/payments/om/return/
OM_NOTIFY_URL=http://127.0.0.1:8000/payments/om/notify/
OM_CANCEL_URL=http://127.0.0.1:8000/payments/om/return/

# --- 6. PARAMÈTRES SANDBOX ---
OM_ENV=sandbox
```

### 🔑 Points clés de configuration

| Variable | Statut | Description |
|----------|--------|-------------|
| `OM_CLIENT_ID` | ✅ Configuré | ID OAuth obtenu via Orange Developer Portal |
| `OM_CLIENT_SECRET` | ✅ Configuré | Secret OAuth |
| `OM_MERCHANT_KEY` | ✅ Configuré | Clé générée lors de l'ajout de l'API Orange Money WebPay Dev |
| `OM_OAUTH_URL` | ✅ Configuré | `https://api.orange.com/oauth/v2/token` |
| `OM_WEBPAY_URL` | ✅ Configuré | `/dev/v1/webpayment` (Sandbox) |
| `OM_TRANSACTION_STATUS_URL` | ✅ Configuré | `/dev/v1/transactionstatus` (Sandbox) |
| `OM_TEST_PUBLIC_URL` | ✅ Configuré | URL de test pour éviter le blocage localhost |

---

## 🔄 Flux de paiement implémenté

### Vue d'ensemble

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌──────────────┐
│  Utilisateur│      │ AuditShield  │      │  Orange Money   │      │  Simulateur  │
│             │      │   (Django)   │      │   API Sandbox   │      │     OTP      │
└──────┬──────┘      └──────┬───────┘      └────────┬────────┘      └──────┬───────┘
       │                    │                       │                       │
       │ 1. Acheter ebook   │                       │                       │
       ├───────────────────>│                       │                       │
       │                    │                       │                       │
       │                    │ 2. OAuth: get token   │                       │
       │                    │──────────────────────>│                       │
       │                    │<──────────────────────│                       │
       │                    │  access_token         │                       │
       │                    │                       │                       │
       │                    │ 3. POST /webpayment   │                       │
       │                    │──────────────────────>│                       │
       │                    │<──────────────────────│                       │
       │                    │  pay_token, notif_token                      │
       │                    │  payment_url          │                       │
       │                    │                       │                       │
       │ 4. Redirection     │                       │                       │
       │<───────────────────┤                       │                       │
       │ vers payment_url   │                       │                       │
       │                    │                       │                       │
       │ 5. Page Orange Money (entre MSISDN + OTP) │                       │
       │────────────────────────────────────────────>│                       │
       │                    │                       │                       │
       │                    │                       │  6. Générer OTP       │
       │                    │                       │<──────────────────────│
       │                    │                       │                       │
       │ 7. Valider (Confirmer)                     │                       │
       │────────────────────────────────────────────>│                       │
       │                    │                       │                       │
       │                    │ 8. Webhook POST /notify/                     │
       │                    │<──────────────────────│                       │
       │                    │  {status: SUCCESS}    │                       │
       │                    │                       │                       │
       │                    │ 9. Mark order PAID    │                       │
       │                    │    Send email         │                       │
       │                    │                       │                       │
       │ 10. Redirection    │                       │                       │
       │<───────────────────│                       │                       │
       │ return_url         │                       │                       │
       │                    │                       │                       │
```

### Détail des étapes

#### **Étape 1-2 : Authentification OAuth 2.0**

**Fichier** : `store/services/orange_money.py` → fonction `get_access_token()`

**Requête** :
```http
POST https://api.orange.com/oauth/v2/token
Authorization: Basic base64(client_id:client_secret)
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```

**Réponse** :
```json
{
  "access_token": "IW3gdUVOvQVcO7mGNsOZgwdhDNvE",
  "token_type": "Bearer",
  "expires_in": 7776000
}
```

**Cache** : Le token est mis en cache Django pendant ~90 jours (ou jusqu'à expiration - 1h)

---

#### **Étape 3 : Création du paiement**

**Fichier** : `store/services/orange_money.py` → fonction `create_payment_request()`

**Requête** :
```http
POST https://api.orange.com/orange-money-webpay/dev/v1/webpayment
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "merchant_key": "xxxxxxxx",
  "currency": "OUV",                    # ⚠️ OUV en sandbox, XOF en production
  "order_id": "abc-def-123...",         # UUID unique (max 30 chars)
  "amount": 15000,                      # Montant en FCFA (entier)
  "return_url": "http://myvirtualshop.webnode.es/payments/om/return/",
  "cancel_url": "http://myvirtualshop.webnode.es/payments/om/return/",
  "notif_url": "http://myvirtualshop.webnode.es/payments/om/notify/",
  "lang": "fr",
  "reference": "AuditShield"            # Nom marchand (max 30 chars)
}
```

**Réponse attendue** :
```json
{
  "status": 201,
  "message": "OK",
  "pay_token": "f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a",
  "payment_url": "https://webpayment-qualif.orange-money.com/payment/pay_token/...",
  "notif_token": "dd497bda3b250e536186fc0663f32f40"
}
```

**⚠️ Particularité Sandbox** : Le code reconstruit l'URL de paiement sandbox :
```
https://webpayment-ow-sb.orange-money.com/payment/pay_token/{pay_token}
```

---

#### **Étape 4-7 : Redirection et validation utilisateur**

1. L'utilisateur est redirigé vers `payment_url`
2. Page Orange Money affichée (entrée MSISDN + OTP)
3. Utilisateur accède au **Simulateur OTP** : https://mpayment.orange-money.com/mpayment-otp/login
   - **Login** : `7701900100` (Merchant Account Number)
   - **Password** : `MerchantWP00100` (Channel User ID)
4. Génère un OTP avec le PIN du Subscriber (`4940`)
5. Entre MSISDN + OTP sur la page Orange Money
6. Clique sur **"Confirmer"**

---

#### **Étape 8 : Webhook (notification)**

**Fichier** : `store/payment_views.py` → fonction `orange_notify()`

**Requête reçue** :
```http
POST http://myvirtualshop.webnode.es/payments/om/notify/
Content-Type: application/json

{
  "status": "SUCCESS",
  "notif_token": "dd497bda3b250e536186fc0663f32f40",
  "txnid": "MP150709.1341.A00073"
}
```

**Traitement** :
1. ✅ Parse le payload JSON
2. ✅ Vérifie que `notif_token` correspond au token stocké lors de la création
3. ✅ Récupère l'Order via `order_id`
4. ✅ Si `status == "SUCCESS"` :
   - Marque l'Order comme `PAID`
   - Crée un `DownloadToken` pour l'ebook
   - Envoie l'email avec les liens de téléchargement
5. ✅ Répond `{"status": "ok"}` (HTTP 200)

**⚠️ Sécurité** : Le `notif_token` est la seule source de validation (pas de vérification HMAC dans le guide Orange)

---

#### **Étape 9-10 : Retour utilisateur**

**Fichier** : `store/payment_views.py` → fonction `orange_return()`

**Requête reçue** :
```
GET http://myvirtualshop.webnode.es/payments/om/return/?order_id=abc-def-123
```

**Comportement** :
- ✅ Affiche "Paiement en cours de validation"
- ⚠️ **Ne valide PAS** le paiement (seul le webhook valide)
- ✅ Informe l'utilisateur d'attendre l'email de confirmation

---

## 🧪 Scénarios de test implémentés

### Commande de test Django

**Fichier** : `store/management/commands/test_orange_money_sandbox.py`

```bash
# Créer un paiement de test (montant: 100 FCFA)
python manage.py test_orange_money_sandbox --amount 100

# Vérifier le statut d'une transaction
python manage.py test_orange_money_sandbox \
  --check-status ORDER_ID \
  --pay-token PAY_TOKEN
```

### Résultat attendu

```
=== Test Orange Money Sandbox (montant: 100 FCFA) ===

✓ Configuration chargée
  - OAuth URL: https://api.orange.com/oauth/v2/token
  - WebPay URL: https://api.orange.com/orange-money-webpay/dev/v1/webpayment

--- Création de l'Order de test ---
✓ Order créé: 123 (uuid: abc-def-...)

--- Appel API Orange Money WebPay Dev ---
✓ Paiement créé avec succès

=== RÉSULTATS ===
Status Code: 201
Message: OK

Order ID: abc-def-123
Pay Token: f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a
Notif Token: dd497bda3b250e536186fc0663f32f40

Payment URL:
https://webpayment-ow-sb.orange-money.com/payment/pay_token/f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a

=== PROCHAINES ÉTAPES ===
1. Copiez la payment_url ci-dessus
2. Ouvrez-la dans votre navigateur
3. Connectez-vous au simulateur OTP:
   https://mpayment.orange-money.com/mpayment-otp/login
4. Utilisez les identifiants Channel User fournis par Orange
5. Générez un OTP et validez la transaction
```

---

## 📊 Statuts de transaction

### Statuts Orange Money

| Statut | Description | Action AuditShield |
|--------|-------------|-------------------|
| `INITIATED` | En attente d'entrée utilisateur | Aucune action |
| `PENDING` | Transaction en cours (utilisateur a cliqué "Confirmer") | Aucune action |
| `EXPIRED` | Token expiré (>10 minutes) | Aucune action |
| `SUCCESS` | ✅ Paiement réussi | ✅ Valider la commande + envoyer l'email |
| `FAILED` | ❌ Paiement échoué | ❌ Informer l'utilisateur |

### Mapping dans le code

**Fichier** : `store/services/orange_money.py` → fonction `map_provider_status_to_paid()`

```python
def map_provider_status_to_paid(provider_status: str) -> bool:
    paid_statuses = ["PAID", "SUCCESS", "COMPLETED", "ACCEPTED", "CONFIRMED", "SUCCESSFUL"]
    return provider_status.upper() in paid_statuses
```

---

## 🛠️ Gestion des URLs localhost (problème connu)

### Problème

Orange Money **n'accepte PAS** les URLs contenant `localhost` ou `127.0.0.1` pour :
- `return_url`
- `cancel_url`
- `notif_url`

### Solutions implémentées

#### **Solution 1 : URL publique de test (recommandé pour sandbox)**

```bash
# Dans .env
OM_TEST_PUBLIC_URL=http://myvirtualshop.webnode.es
```

**Comportement** :
- Le code détecte automatiquement si les URLs contiennent `localhost/127.0.0.1`
- Remplace par l'URL publique de test configurée
- ⚠️ Les webhooks ne seront pas reçus (URL de test ne pointe pas vers notre serveur)
- ✅ Permet de tester l'API Orange Money sans erreur

#### **Solution 2 : ngrok (recommandé pour recevoir les webhooks)**

```bash
# 1. Installer ngrok
# https://ngrok.com/

# 2. Lancer ngrok
ngrok http 8000

# 3. Copier l'URL HTTPS générée
# Exemple: https://xxxx.ngrok.io

# 4. Configurer dans .env
OM_NGROK_URL=https://xxxx.ngrok.io
```

**Comportement** :
- Le code détecte `OM_NGROK_URL` et l'utilise pour `notif_url`
- ✅ Les webhooks sont reçus en local
- ✅ Permet de tester le flux complet

#### **Solution 3 : Fallback automatique**

Si aucune URL n'est configurée, le code utilise par défaut :
```
http://myvirtualshop.webnode.es
```

---

## 🔍 Logging et débogage

### Logs structurés

Tous les appels API sont loggés avec le format :
```
[OM][nom_fonction] Message détaillé | key1=value1 | key2=value2
```

**Exemples** :
```
[OM][OAuth] Requesting token from https://api.orange.com/oauth/v2/token
[OM][OAuth] Token obtenu avec succès (cache pour 7776000s)

[OM][create_payment] Initiating payment: order_id=abc-def-123, amount=15000 XOF
[OM][create_payment] Payment créé avec succès | payment_url=https://... | pay_token=f5720dd...

[OM][check_status] Checking status | order_id=abc-def-123 | amount=15000 | pay_token=f5720dd...
[OM][check_status] Status retrieved | order_id=abc-def-123 | status=SUCCESS | txnid=MP150709.1341.A00073

[OM][verify_webhook] Payload reçu | status=SUCCESS | notif_token=dd497b... | txnid=MP150709.1341.A00073
```

### Activer les logs détaillés

```python
# Dans settings/dev.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'store.services.orange_money': {
            'handlers': ['console'],
            'level': 'DEBUG',  # ← Activer DEBUG pour voir tous les logs
        },
    },
}
```

---

## ⚠️ Points d'attention et problèmes connus

### 1. ❌ Erreur OAuth (401/403)

**Causes possibles** :
- `OM_CLIENT_ID` ou `OM_CLIENT_SECRET` incorrects
- Endpoint OAuth incorrect (doit être `/oauth/v2/token`)

**Solutions** :
1. Vérifier les identifiants sur Orange Developer Portal
2. Vérifier `OM_OAUTH_URL=https://api.orange.com/oauth/v2/token`
3. Vider le cache du token :
   ```python
   from django.core.cache import cache
   cache.delete('orange_money_access_token')
   ```

### 2. ❌ Erreur API WebPay (400/401/403)

**Causes possibles** :
- `OM_MERCHANT_KEY` incorrecte
- Champs manquants ou invalides dans le payload
- URLs `return_url`/`notif_url` contenant localhost (non acceptées)

**Solutions** :
1. Vérifier `OM_MERCHANT_KEY` sur Orange Developer Portal
2. Vérifier les logs pour voir le payload envoyé
3. Configurer `OM_TEST_PUBLIC_URL` ou `OM_NGROK_URL`

### 3. ⚠️ Webhook non reçu

**Causes possibles** :
- `notif_url` n'est pas accessible publiquement (localhost)
- Problème réseau/firewall
- Transaction non validée (statut reste `INITIATED`)

**Solutions** :
1. Utiliser `ngrok` pour exposer le serveur local
2. Vérifier que la transaction a été validée (statut `SUCCESS`)
3. Vérifier les logs Django pour voir si le webhook est reçu

### 4. ⚠️ Payment URL ne se charge pas (timeout)

**Causes possibles** :
- URL retournée par l'API incorrecte
- `pay_token` expiré (>10 minutes)

**Solutions** :
1. Vérifier les logs Django pour voir l'URL exacte retournée
2. Vérifier que vous utilisez bien l'URL retournée par l'API
3. Tester avec une nouvelle transaction

---

## 📞 Support et contacts

### Ressources techniques

| Ressource | Lien/Contact |
|-----------|--------------|
| **Simulateur OTP** | https://mpayment.orange-money.com/mpayment-otp/login |
| **Orange Developer Portal** | https://developer.orange.com/myapps |
| **Support Orange** | georgiana.cruceru@orange.com |
| **Guide officiel** | `guide_orange.md` (dans le projet) |
| **Guide sandbox** | `docs/orange_money_sandbox.md` |

### Identifiants de test (à demander par email)

Si vous n'avez pas reçu les identifiants, contactez **georgiana.cruceru@orange.com** pour obtenir :

**Channel User** (Merchant) :
- ID/Login : `MerchantWP00100` (exemple)
- Merchant Account Number : `7701900100` (exemple)
- Merchant Code : `101021` (exemple)
- PIN code : `xxxx` (fourni par Orange)

**Subscriber** (Client) :
- MSISDN : `7701100100` (exemple)
- PIN : `xxxx` (fourni par Orange)

---

## ✅ Checklist d'intégration

### Configuration initiale

- [x] Application créée sur Orange Developer Portal
- [x] API "Orange Money WebPay Dev" ajoutée à l'application
- [x] `OM_CLIENT_ID` et `OM_CLIENT_SECRET` obtenus (OAuth)
- [x] `OM_MERCHANT_KEY` générée
- [x] Variables d'environnement configurées dans `.env`
- [x] Identifiants de test reçus (Channel User + Subscriber)

### Implémentation

- [x] Service `orange_money.py` implémenté
- [x] Authentification OAuth 2.0 fonctionnelle
- [x] Création de paiement WebPay Dev implémentée
- [x] Webhook de notification implémenté
- [x] Vérification de statut implémentée
- [x] Gestion des URLs localhost (fallback automatique)
- [x] Logging structuré mis en place

### Tests

- [x] Commande de test `test_orange_money_sandbox` créée
- [x] Test OAuth réussi (obtention du token)
- [x] Test création de paiement réussi (payment_url retournée)
- [ ] Test validation avec Simulateur OTP (en attente identifiants)
- [ ] Test webhook de notification (en attente identifiants)
- [ ] Test vérification de statut (en attente identifiants)

### Production (à venir)

- [ ] Obtenir les identifiants de production
- [ ] Changer les endpoints (`/dev/v1/` → `/v1/`)
- [ ] Changer la devise (`OUV` → `XOF`)
- [ ] Configurer des URLs HTTPS publiques
- [ ] Tester en environnement de production

---

## 📝 Résumé pour les agents Orange

### Ce qui est implémenté ✅

1. ✅ **Authentification OAuth 2.0** avec cache de token (90 jours)
2. ✅ **Création de paiement** via `/dev/v1/webpayment`
3. ✅ **Webhook de notification** avec vérification `notif_token`
4. ✅ **Vérification de statut** via `/dev/v1/transactionstatus`
5. ✅ **Gestion automatique des URLs localhost** (fallback vers URL de test)
6. ✅ **Logging complet** pour le débogage
7. ✅ **Commande de test** pour valider l'intégration

### Ce qui est attendu ⏳

1. ⏳ **Identifiants de test** (Channel User + Subscriber) pour valider le flux complet
2. ⏳ **Test E2E avec Simulateur OTP** pour générer et valider un paiement
3. ⏳ **Validation du format webhook** (réponse réelle d'Orange Money)
4. ⏳ **Identifiants de production** pour déployer en production

### Configuration actuelle

| Paramètre | Valeur |
|-----------|--------|
| **Mode** | Sandbox (`/dev/v1/`) |
| **Devise** | `OUV` (sandbox) |
| **OAuth URL** | `https://api.orange.com/oauth/v2/token` |
| **WebPay URL** | `https://api.orange.com/orange-money-webpay/dev/v1/webpayment` |
| **Status URL** | `https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus` |
| **Payment URL** | `https://webpayment-ow-sb.orange-money.com/payment/pay_token/{pay_token}` |

---

## 📄 Annexes

### A. Exemple de requête OAuth

```bash
curl -X POST https://api.orange.com/oauth/v2/token \
  -H "Authorization: Basic $(echo -n 'client_id:client_secret' | base64)" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials"
```

### B. Exemple de requête WebPay

```bash
curl -X POST https://api.orange.com/orange-money-webpay/dev/v1/webpayment \
  -H "Authorization: Bearer IW3gdUVOvQVcO7mGNsOZgwdhDNvE" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_key": "xxxxxxxx",
    "currency": "OUV",
    "order_id": "TEST_001",
    "amount": 1500,
    "return_url": "http://myvirtualshop.webnode.es/return",
    "cancel_url": "http://myvirtualshop.webnode.es/cancel",
    "notif_url": "http://myvirtualshop.webnode.es/notif",
    "lang": "fr",
    "reference": "AuditShield"
  }'
```

### C. Exemple de webhook

```bash
curl -X POST http://myvirtualshop.webnode.es/payments/om/notify/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "SUCCESS",
    "notif_token": "dd497bda3b250e536186fc0663f32f40",
    "txnid": "MP150709.1341.A00073"
  }'
```

---

**Document préparé pour** : Agents Orange Money  
**Date** : 4 décembre 2024  
**Version** : 1.0.0 (Sandbox)  
**Contact** : AuditShield Dev Team

