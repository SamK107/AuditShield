# Comment tester Orange Money en mode Sandbox

Ce guide explique comment tester l'intégration Orange Money WebPay Dev (Sandbox) dans AuditShield.

## Prérequis

1. **Compte Orange Developer** avec accès à l'API Orange Money WebPay Dev
2. **Identifiants fournis par Orange** :
   - `OM_CLIENT_ID` : ID de votre application Orange Developer
   - `OM_CLIENT_SECRET` : Secret de votre application
   - `OM_MERCHANT_KEY` : Clé marchand générée sur Orange Developer
   - **Channel User** (pour le simulateur OTP) :
     - ID/Login : `MerchantWP00100` (exemple)
     - Merchant Account Number : `7701900100` (exemple)
     - Merchant Code : `101021` (exemple)
     - PIN code : `xxxx` (fourni par Orange)
   - **Subscriber** (pour le simulateur OTP) :
     - MSISDN : `7701100100` (exemple)
     - PIN : `xxxx` (fourni par Orange)

3. **Variables d'environnement configurées** (voir `ENV_TEMPLATE.txt`) :
   ```bash
   OM_CLIENT_ID=votre_client_id
   OM_CLIENT_SECRET=votre_client_secret
   OM_MERCHANT_KEY=votre_merchant_key
   OM_RETURN_URL=https://votre-domaine.com/payments/om/return/
   OM_NOTIFY_URL=https://votre-domaine.com/payments/om/notify/
   ```

## Configuration

### 1. Variables d'environnement requises

Ajoutez ces variables dans votre fichier `.env` ou dans les variables d'environnement de votre serveur :

```bash
# OAuth / Access Token
OM_CLIENT_ID=votre_client_id
OM_CLIENT_SECRET=votre_client_secret
OM_OAUTH_URL=https://api.orange.com/oauth/v2/token

# WebPay Dev (Sandbox)
OM_MERCHANT_KEY=votre_merchant_key
OM_WEBPAY_URL=https://api.orange.com/orange-money-webpay/dev/v1/webpayment
OM_TRANSACTION_STATUS_URL=https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus

# URLs de retour (doivent être publiques en HTTPS pour recevoir les webhooks)
OM_RETURN_URL=https://votre-domaine.com/payments/om/return/
OM_NOTIFY_URL=https://votre-domaine.com/payments/om/notify/
OM_CANCEL_URL=https://votre-domaine.com/payments/om/return/  # Peut être identique à return_url

# Pour le développement local avec ngrok
OM_NGROK_URL=https://xxxx.ngrok.io  # Optionnel, pour recevoir les webhooks en local
OM_TEST_PUBLIC_URL=https://votre-site-test.com  # Optionnel, pour les tests
```

**Important** :
- En mode sandbox, la devise doit être `OUV` (gérée automatiquement par le code)
- Les URLs `return_url`, `cancel_url` et `notif_url` doivent être publiques (pas `localhost` ou `127.0.0.1`)
- Pour le développement local, utilisez `ngrok` ou une URL de test publique

### 2. Générer/Rafraîchir le token OAuth

Le token OAuth est automatiquement mis en cache et réutilisé jusqu'à expiration (~90 jours selon le guide Orange).

Pour forcer un nouveau token, videz le cache Django :
```bash
python manage.py shell
>>> from django.core.cache import cache
>>> cache.delete('orange_money_access_token')
```

## Scénario de test complet

### Étape 1 : Créer un paiement de test

Utilisez la commande de test fournie :

```bash
python manage.py test_orange_money_sandbox --amount 100
```

Cette commande :
1. Vérifie la configuration
2. Crée un Order de test (montant 100 FCFA, currency OUV en sandbox)
3. Appelle l'API Orange Money WebPay Dev
4. Affiche la `payment_url` retournée par l'API
5. Affiche le `pay_token` et `notif_token` pour référence

**Exemple de sortie** :
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

### Étape 2 : Ouvrir la payment_url

Copiez la `payment_url` affichée et ouvrez-la dans votre navigateur.

Vous devriez voir la page de paiement Orange Money avec :
- Le montant à payer
- Un champ pour entrer votre numéro de téléphone (MSISDN)
- Un champ pour entrer l'OTP

### Étape 3 : Utiliser le simulateur OTP

1. **Accéder au simulateur** :
   - URL : https://mpayment.orange-money.com/mpayment-otp/login
   - Login : Utilisez le **Merchant Account Number** (ex: `7701900100`)
   - Password : Utilisez le **Channel User ID** (ex: `MerchantWP00100`)

2. **Générer un OTP** :
   - Entrez le **PIN du Subscriber** (fourni par Orange)
   - Cliquez sur "Request OTP"
   - Un code OTP sera généré

3. **Valider la transaction** :
   - Retournez sur la page de paiement Orange Money
   - Entrez le **MSISDN du Subscriber** (ex: `7701100100`)
   - Entrez l'**OTP** généré
   - Cliquez sur "Confirmer"

### Étape 4 : Vérifier le statut de la transaction

Après avoir validé la transaction, vérifiez son statut :

```bash
python manage.py test_orange_money_sandbox \
  --check-status ORDER_ID \
  --pay-token PAY_TOKEN
```

**Exemple** :
```bash
python manage.py test_orange_money_sandbox \
  --check-status abc-def-123 \
  --pay-token f5720dd906203c62033ffe64ed75614785878b0ab2231d9c582b2908fca0ab9a
```

**Statuts possibles** :
- `INITIATED` : En attente d'entrée utilisateur
- `PENDING` : Transaction en cours (utilisateur a cliqué sur Confirmer)
- `EXPIRED` : Token expiré (utilisateur a cliqué trop tard, >10 minutes)
- `SUCCESS` : Paiement réussi ✓
- `FAILED` : Paiement échoué ✗

### Étape 5 : Vérifier la notification webhook

Si la transaction est validée avec succès, Orange Money enverra une notification POST à votre `notif_url`.

**Format de la notification** (selon guide section 3.3) :
```json
{
  "status": "SUCCESS",
  "notif_token": "dd497bda3b250e536186fc0663f32f40",
  "txnid": "MP150709.1341.A00073"
}
```

**Vérifications effectuées par le code** :
1. Le `notif_token` reçu doit correspondre au `notif_token` retourné lors de la création du paiement
2. Le statut est mappé vers `PAID` ou `FAILED`
3. L'Order est mis à jour en base de données
4. Le fulfillment est déclenché (email de livraison, etc.)

## Dépannage

### Problème : La payment_url ne se charge pas (timeout)

**Causes possibles** :
1. L'URL retournée par l'API est incorrecte
2. Problème réseau/firewall
3. Le `pay_token` est invalide ou expiré

**Solutions** :
1. Vérifiez les logs Django pour voir l'URL exacte retournée par l'API
2. Vérifiez que vous utilisez bien l'URL retournée par l'API (ne pas la modifier)
3. Vérifiez que le `pay_token` est valide (pas expiré, <10 minutes)
4. Testez avec une nouvelle transaction

### Problème : Erreur OAuth (401, 403)

**Causes possibles** :
1. `OM_CLIENT_ID` ou `OM_CLIENT_SECRET` incorrects
2. L'endpoint OAuth est incorrect (doit être `/oauth/v2/token`)

**Solutions** :
1. Vérifiez vos identifiants sur Orange Developer Portal
2. Vérifiez que `OM_OAUTH_URL` est bien `https://api.orange.com/oauth/v2/token`
3. Videz le cache du token et réessayez

### Problème : Erreur API WebPay (400, 401, 403)

**Causes possibles** :
1. `OM_MERCHANT_KEY` incorrecte
2. Champs manquants ou invalides dans le payload
3. URLs `return_url`/`notif_url` invalides (localhost non accepté)

**Solutions** :
1. Vérifiez votre `OM_MERCHANT_KEY` sur Orange Developer Portal
2. Vérifiez les logs pour voir le payload envoyé
3. Utilisez des URLs publiques (ngrok ou URL de test) pour `return_url` et `notif_url`

### Problème : Le webhook n'est pas reçu

**Causes possibles** :
1. L'URL `notif_url` n'est pas accessible publiquement
2. Problème de firewall/réseau
3. La transaction n'a pas été validée (statut reste `INITIATED`)

**Solutions** :
1. Utilisez `ngrok` pour exposer votre serveur local :
   ```bash
   ngrok http 8000
   # Puis configurez OM_NOTIFY_URL=https://xxxx.ngrok.io/payments/om/notify/
   ```
2. Vérifiez que la transaction a bien été validée (statut `SUCCESS`)
3. Vérifiez les logs Django pour voir si le webhook est reçu

### Problème : notif_token ne correspond pas

**Causes possibles** :
1. Le `notif_token` n'a pas été stocké lors de la création du paiement
2. Le webhook provient d'une autre transaction

**Solutions** :
1. Vérifiez que le `notif_token` est bien stocké dans `Payment.raw_response`
2. Vérifiez que vous utilisez le bon `order_id` pour retrouver l'Order

## Points importants selon le guide officiel

### 1. OAuth / Access Token
- ✅ Endpoint : `https://api.orange.com/oauth/v2/token`
- ✅ Authentification : Basic avec `client_id:client_secret`
- ✅ Grant type : `client_credentials`
- ✅ Token mis en cache et réutilisé jusqu'à expiration (~90 jours)

### 2. Web Payment – Sandbox / Dev
- ✅ Endpoint : `https://api.orange.com/orange-money-webpay/dev/v1/webpayment`
- ✅ Méthode : POST JSON
- ✅ Headers : `Authorization: Bearer <access_token>`, `Accept: application/json`, `Content-Type: application/json`
- ✅ Currency : `OUV` en sandbox (géré automatiquement)
- ✅ Status attendu : `201` (pas `200`)

### 3. Redirection vers la page de paiement
- ✅ Utiliser exactement le champ `payment_url` retourné par l'API
- ✅ Ne pas modifier ou reconstruire l'URL manuellement

### 4. Notification + Transaction Status
- ✅ Vérifier que le `notif_token` correspond
- ✅ Mettre à jour le statut de la transaction en base
- ✅ Endpoint de statut : `https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus`
- ✅ Inclure `order_id`, `amount` et `pay_token` dans la requête de statut

## Commandes utiles

```bash
# Créer un paiement de test (montant par défaut: 100 FCFA)
python manage.py test_orange_money_sandbox

# Créer un paiement de test avec un montant spécifique
python manage.py test_orange_money_sandbox --amount 500

# Vérifier le statut d'une transaction
python manage.py test_orange_money_sandbox --check-status ORDER_ID --pay-token PAY_TOKEN

# Vider le cache du token OAuth (pour forcer un nouveau token)
python manage.py shell
>>> from django.core.cache import cache
>>> cache.delete('orange_money_access_token')
```

## Ressources

- **Guide officiel Orange** : `guide_orange.md` (dans le projet)
- **Simulateur OTP** : https://mpayment.orange-money.com/mpayment-otp/login
- **Orange Developer Portal** : https://developer.orange.com/myapps
- **Support Orange** : georgiana.cruceru@orange.com (pour obtenir les identifiants Channel User et Subscriber)

