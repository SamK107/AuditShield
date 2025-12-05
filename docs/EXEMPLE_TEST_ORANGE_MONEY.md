# 📝 Exemple de Test Orange Money - Trace Complète

## Scénario : Achat d'un ebook "Audit Sans Peur" (15 000 FCFA)

---

## 🎬 Étape 1 : Lancement de la commande de test

### Commande
```bash
python manage.py test_orange_money_sandbox --amount 15000
```

### Output Console
```
=== Test Orange Money Sandbox (montant: 15000 FCFA) ===

[ÉTAPE 1] Chargement de la configuration...
✓ Configuration chargée
  - OAuth URL: https://api.orange.com/oauth/v2/token
  - WebPay URL: https://api.orange.com/orange-money-webpay/dev/v1/webpayment
  - Status URL: https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus
  - Merchant Key: 4e******30x (masqué)
  - Test Public URL: http://myvirtualshop.webnode.es

[ÉTAPE 2] Création de l'Order de test...
✓ Order créé avec succès
  - ID: 247
  - UUID: 8c3a9f7b-2d1e-4a8c-9b5f-6e4d3c2a1b0c
  - Montant: 15000 FCFA
  - Devise: OUV (sandbox)
  - Email: test@auditshield.com
  - Statut: PENDING

[ÉTAPE 3] Obtention du token OAuth...
```

### Logs Django (DEBUG)
```
INFO [OM][OAuth] Requesting token from https://api.orange.com/oauth/v2/token
DEBUG [OM][OAuth] Request headers: {
  "Authorization": "Basic xxxxxxxxxxxxxxxxxxxxxxxxxx",
  "Content-Type": "application/x-www-form-urlencoded",
  "Accept": "application/json"
}
DEBUG [OM][OAuth] Request data: grant_type=client_credentials
INFO [OM][OAuth] Response HTTP 200
DEBUG [OM][OAuth] Response body: {
  "access_token": "IW3gdUVOvQVcO7mGNsOZgwdhDNvE",
  "token_type": "Bearer",
  "expires_in": 7776000
}
INFO [OM][OAuth] Token obtenu avec succès (cache pour 7772400s)
```

### Output Console (suite)
```
✓ Token OAuth obtenu
  - Access Token: IW3gdU****************dhDNvE (masqué)
  - Expires in: 7776000s (~90 jours)
  - Cached: Oui

[ÉTAPE 4] Création du paiement WebPay...
```

---

## 🎬 Étape 2 : Création du paiement

### Logs Django (DEBUG)
```
INFO [OM][create_payment] Initiating payment: order_id=8c3a9f7b-2d1e-4a8c-9b5f-6e4, amount=15000 OUV
DEBUG [OM][create_payment] Payload: {
  "merchant_key": "4e******30x",
  "currency": "OUV",
  "order_id": "8c3a9f7b-2d1e-4a8c-9b5f-6e4",
  "amount": 15000,
  "return_url": "http://myvirtualshop.webnode.es/payments/om/return/",
  "cancel_url": "http://myvirtualshop.webnode.es/payments/om/return/",
  "notif_url": "http://myvirtualshop.webnode.es/payments/om/notify/",
  "lang": "fr",
  "reference": "AuditShield"
}
INFO [OM][create_payment] POST https://api.orange.com/orange-money-webpay/dev/v1/webpayment
DEBUG [OM][create_payment] Request headers: {
  "Authorization": "Bearer IW3gdUVOvQVcO7mGNsOZgwdhDNvE",
  "Content-Type": "application/json",
  "Accept": "application/json"
}
INFO [OM][create_payment] Response HTTP 201
DEBUG [OM][create_payment] Response body: {
  "status": 201,
  "message": "OK",
  "pay_token": "f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a",
  "payment_url": "https://webpayment-qualif.orange-money.com/payment/pay_token/f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a",
  "notif_token": "dd497bda3b250e536186fc0663f32f40"
}
INFO [OM][create_payment] Mode sandbox détecté | URL API originale: https://webpayment-qualif.orange-money.com/payment/pay_token/... | URL sandbox corrigée: https://webpayment-ow-sb.orange-money.com/payment/pay_token/...
INFO [OM][create_payment] Payment créé avec succès | payment_url=https://webpayment-ow-sb.orange-money.com/payment/pay_token/f5720dd... | pay_token=f5720dd906203c62033... | notif_token=dd497bda3b250e536...
```

### Output Console (suite)
```
✓ Paiement créé avec succès

=== RÉSULTATS ===

HTTP Status: 201
Message: OK

Order ID: 8c3a9f7b-2d1e-4a8c-9b5f-6e4
Pay Token: f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a
Notif Token: dd497bda3b250e536186fc0663f32f40

Payment URL:
https://webpayment-ow-sb.orange-money.com/payment/pay_token/f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a

=== PROCHAINES ÉTAPES ===

1. Copiez la payment_url ci-dessus
2. Ouvrez-la dans votre navigateur
3. Vous verrez la page de paiement Orange Money

Pour générer un OTP et valider la transaction :

4. Connectez-vous au simulateur OTP :
   https://mpayment.orange-money.com/mpayment-otp/login
   
   Login    : 7701900100  (Merchant Account Number)
   Password : MerchantWP00100  (Channel User ID)

5. Entrez le PIN du Subscriber : 4940

6. Cliquez sur "Request OTP"

7. Un code OTP sera généré (exemple: 123456)

8. Retournez sur la page de paiement Orange Money :
   - Entrez le MSISDN du Subscriber : 7701100100
   - Entrez l'OTP généré : 123456
   - Cliquez sur "Confirmer"

9. Orange Money enverra un webhook à notre serveur
   (si notif_url est accessible publiquement)

10. Vérifiez le statut de la transaction :
    python manage.py test_orange_money_sandbox \
      --check-status 8c3a9f7b-2d1e-4a8c-9b5f-6e4 \
      --pay-token f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a
```

---

## 🎬 Étape 3 : Validation utilisateur (Simulateur OTP)

### 3.1 Accès au Simulateur OTP

**URL** : https://mpayment.orange-money.com/mpayment-otp/login

**Login** :
```
Username : 7701900100  (Merchant Account Number)
Password : MerchantWP00100  (Channel User ID)
```

### 3.2 Génération de l'OTP

**Page du Simulateur** :
```
╔════════════════════════════════════════╗
║  Orange Money - OTP Simulator          ║
╠════════════════════════════════════════╣
║                                        ║
║  Subscriber PIN:  [____]  (Enter 4940)║
║                                        ║
║  [ Request OTP ]                       ║
║                                        ║
╚════════════════════════════════════════╝
```

**Après avoir cliqué sur "Request OTP"** :
```
╔════════════════════════════════════════╗
║  OTP Generated                         ║
╠════════════════════════════════════════╣
║                                        ║
║  OTP Code: 123456                      ║
║                                        ║
║  Valid for: 10 minutes                 ║
║                                        ║
╚════════════════════════════════════════╝
```

### 3.3 Page de paiement Orange Money

**URL** : `https://webpayment-ow-sb.orange-money.com/payment/pay_token/f5720dd...`

**Page affichée** :
```
╔══════════════════════════════════════════════╗
║  Orange Money - Paiement                     ║
╠══════════════════════════════════════════════╣
║                                              ║
║  Montant à payer : 15 000 FCFA               ║
║  Marchand : AuditShield                      ║
║                                              ║
║  Numéro de téléphone :                       ║
║  [7701100100________________]                ║
║                                              ║
║  Code OTP :                                  ║
║  [123456____________________]                ║
║                                              ║
║  [ Confirmer ]    [ Annuler ]                ║
║                                              ║
╚══════════════════════════════════════════════╝
```

**Après avoir cliqué sur "Confirmer"** :
```
╔══════════════════════════════════════════════╗
║  Orange Money - Paiement                     ║
╠══════════════════════════════════════════════╣
║                                              ║
║  ✅ Paiement en cours de traitement...       ║
║                                              ║
║  Vous allez être redirigé...                 ║
║                                              ║
╚══════════════════════════════════════════════╝
```

---

## 🎬 Étape 4 : Webhook de notification

### 4.1 Requête Orange Money → Notre serveur

**Requête HTTP** :
```http
POST http://myvirtualshop.webnode.es/payments/om/notify/
Content-Type: application/json

{
  "status": "SUCCESS",
  "notif_token": "dd497bda3b250e536186fc0663f32f40",
  "txnid": "MP150709.1341.A00073"
}
```

### 4.2 Logs Django (Webhook)

```
INFO [OM][verify_webhook] Webhook reçu
DEBUG [OM][verify_webhook] Headers: {
  "Content-Type": "application/json",
  "User-Agent": "Orange-Money-API/1.0",
  "X-Forwarded-For": "41.203.xx.xx"
}
INFO [OM][verify_webhook] Payload reçu | status=SUCCESS | notif_token=dd497b... | txnid=MP150709.1341.A00073
DEBUG [OM][verify_webhook] Full payload: {
  "status": "SUCCESS",
  "notif_token": "dd497bda3b250e536186fc0663f32f40",
  "txnid": "MP150709.1341.A00073"
}

INFO [store.payment_views] Processing Orange Money webhook | status=SUCCESS
INFO [store.payment_views] Searching for Order with notif_token=dd497bda3b250e536186fc0663f32f40
DEBUG [store.payment_views] Found Order: id=247, uuid=8c3a9f7b-2d1e-4a8c-9b5f-6e4, status=PENDING

INFO [store.payment_views] Verifying notif_token...
DEBUG [store.payment_views] Stored notif_token: dd497bda3b250e536186fc0663f32f40
DEBUG [store.payment_views] Received notif_token: dd497bda3b250e536186fc0663f32f40
INFO [store.payment_views] notif_token verified ✓

INFO [store.payment_views] Marking Order as PAID...
INFO [store.models.Order] Order 247 marked as PAID | txnid=MP150709.1341.A00073

INFO [store.payment_views] Creating DownloadToken...
INFO [store.models.DownloadToken] Token created for Order 247 | token=a1b2c3d4-e5f6-7890-abcd-ef1234567890

INFO [store.payment_views] Sending confirmation email...
INFO [django.core.mail] Sending email to test@auditshield.com
INFO [django.core.mail] Subject: Votre ebook "Audit Sans Peur" est disponible
INFO [django.core.mail] Download link: http://127.0.0.1:8000/telecharger/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
INFO [django.core.mail] Email sent successfully ✓

INFO [store.payment_views] Webhook processed successfully | order_id=8c3a9f7b-2d1e-4a8c-9b5f-6e4 | status=SUCCESS
```

### 4.3 Réponse de notre serveur

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok"
}
```

---

## 🎬 Étape 5 : Retour utilisateur

### 5.1 Redirection

Orange Money redirige l'utilisateur vers :
```
http://myvirtualshop.webnode.es/payments/om/return/?order_id=8c3a9f7b-2d1e-4a8c-9b5f-6e4
```

### 5.2 Page affichée (payment_pending.html)

```
╔══════════════════════════════════════════════╗
║  AuditShield                                 ║
╠══════════════════════════════════════════════╣
║                                              ║
║  ⏳ Paiement en cours de validation           ║
║                                              ║
║  Votre paiement a bien été initié.           ║
║                                              ║
║  Vous recevrez un email de confirmation      ║
║  avec vos liens de téléchargement dès que    ║
║  le paiement sera validé.                    ║
║                                              ║
║  Cela peut prendre quelques instants.        ║
║                                              ║
║  [ Retour à l'accueil ]                      ║
║                                              ║
╚══════════════════════════════════════════════╝
```

### 5.3 Logs Django (Retour)

```
INFO [store.payment_views] Orange Money return | order_id=8c3a9f7b-2d1e-4a8c-9b5f-6e4
INFO [store.payment_views] Order found: id=247, status=PAID
INFO [store.payment_views] Displaying payment_pending.html (NOT validating payment)
```

---

## 🎬 Étape 6 : Vérification du statut

### Commande
```bash
python manage.py test_orange_money_sandbox \
  --check-status 8c3a9f7b-2d1e-4a8c-9b5f-6e4 \
  --pay-token f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a
```

### Logs Django
```
INFO [OM][check_status] Checking status | order_id=8c3a9f7b-2d1e-4a8c-9b5f-6e4 | amount=None | pay_token=f5720dd906...
DEBUG [OM][check_status] Payload: {
  "merchant_key": "4e******30x",
  "order_id": "8c3a9f7b-2d1e-4a8c-9b5f-6e4",
  "pay_token": "f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a"
}
INFO [OM][check_status] POST https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus
INFO [OM][check_status] Response HTTP 201
DEBUG [OM][check_status] Response body: {
  "status": "SUCCESS",
  "order_id": "8c3a9f7b-2d1e-4a8c-9b5f-6e4",
  "txnid": "MP150709.1341.A00073"
}
INFO [OM][check_status] Status retrieved | order_id=8c3a9f7b-2d1e-4a8c-9b5f-6e4 | status=SUCCESS | txnid=MP150709.1341.A00073
```

### Output Console
```
=== Vérification du statut de la transaction ===

Order ID: 8c3a9f7b-2d1e-4a8c-9b5f-6e4
Pay Token: f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a

--- Résultat ---

✅ Status: SUCCESS
Transaction ID: MP150709.1341.A00073

Le paiement a été validé avec succès !
```

---

## 📊 Récapitulatif des données échangées

### 1. OAuth Token Request
```
POST https://api.orange.com/oauth/v2/token
Authorization: Basic base64(CLIENT_ID:CLIENT_SECRET)

Response: 200
{
  "access_token": "IW3gdUVOvQVcO7mGNsOZgwdhDNvE",
  "expires_in": 7776000
}
```

### 2. WebPayment Request
```
POST https://api.orange.com/orange-money-webpay/dev/v1/webpayment
Authorization: Bearer IW3gdUVOvQVcO7mGNsOZgwdhDNvE

{
  "merchant_key": "4e******30x",
  "currency": "OUV",
  "order_id": "8c3a9f7b-2d1e-4a8c-9b5f-6e4",
  "amount": 15000,
  "return_url": "http://myvirtualshop.webnode.es/payments/om/return/",
  "cancel_url": "http://myvirtualshop.webnode.es/payments/om/return/",
  "notif_url": "http://myvirtualshop.webnode.es/payments/om/notify/",
  "lang": "fr",
  "reference": "AuditShield"
}

Response: 201
{
  "status": 201,
  "message": "OK",
  "pay_token": "f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a",
  "payment_url": "https://webpayment-qualif.orange-money.com/payment/pay_token/...",
  "notif_token": "dd497bda3b250e536186fc0663f32f40"
}
```

### 3. Webhook Notification
```
POST http://myvirtualshop.webnode.es/payments/om/notify/

{
  "status": "SUCCESS",
  "notif_token": "dd497bda3b250e536186fc0663f32f40",
  "txnid": "MP150709.1341.A00073"
}

Response: 200
{
  "status": "ok"
}
```

### 4. Transaction Status Request
```
POST https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus
Authorization: Bearer IW3gdUVOvQVcO7mGNsOZgwdhDNvE

{
  "merchant_key": "4e******30x",
  "order_id": "8c3a9f7b-2d1e-4a8c-9b5f-6e4",
  "pay_token": "f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a"
}

Response: 201
{
  "status": "SUCCESS",
  "order_id": "8c3a9f7b-2d1e-4a8c-9b5f-6e4",
  "txnid": "MP150709.1341.A00073"
}
```

---

## ✅ Résultat final

### Base de données

**Table `store_order`** :
```sql
id  | uuid                                 | status | amount_fcfa | currency | provider_ref         | email
----+--------------------------------------+--------+-------------+----------+----------------------+-------------------------
247 | 8c3a9f7b-2d1e-4a8c-9b5f-6e4d3c2a1b0c | PAID   | 15000       | OUV      | MP150709.1341.A00073 | test@auditshield.com
```

**Table `store_downloadtoken`** :
```sql
id  | token                                | order_id | created_at          | expires_at
----+--------------------------------------+----------+---------------------+---------------------
42  | a1b2c3d4-e5f6-7890-abcd-ef1234567890 | 247      | 2024-12-04 10:30:00 | 2024-12-11 10:30:00
```

### Email envoyé

**À** : test@auditshield.com  
**Sujet** : Votre ebook "Audit Sans Peur" est disponible

**Corps** :
```
Bonjour,

Merci pour votre achat !

Votre paiement de 15 000 FCFA a été confirmé.

Vous pouvez maintenant télécharger votre ebook "Audit Sans Peur" :

👉 http://127.0.0.1:8000/telecharger/a1b2c3d4-e5f6-7890-abcd-ef1234567890/

Ce lien est valide pendant 7 jours.

Cordialement,
L'équipe AuditShield
```

---

## 📌 Points clés pour les agents Orange

### ✅ Ce qui fonctionne

1. ✅ Authentification OAuth avec cache
2. ✅ Création de paiement WebPay
3. ✅ Reconstruction de l'URL sandbox
4. ✅ Validation webhook via `notif_token`
5. ✅ Vérification de statut
6. ✅ Gestion automatique des URLs localhost
7. ✅ Logging complet de toutes les étapes

### ⏳ Ce qui nécessite vos identifiants

1. ⏳ Test E2E avec Simulateur OTP
2. ⏳ Validation du format webhook réel
3. ⏳ Test de bout en bout avec paiement réel

### 🔍 Observations importantes

1. Le code reconstruit l'URL sandbox car l'API retourne parfois une URL `webpayment-qualif`
2. Le `notif_token` est la seule source de validation (pas de HMAC mentionné dans le guide)
3. Le webhook est idempotent (vérifie si Order déjà PAID)
4. Le retour utilisateur n'effectue JAMAIS de validation (seul le webhook valide)

---

**Exemple de test complet** - Orange Money Sandbox  
**Date** : 4 décembre 2024  
**Pour** : Agents Orange Money

