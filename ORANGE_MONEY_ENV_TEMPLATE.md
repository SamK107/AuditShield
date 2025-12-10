# Configuration Orange Money WebPay DEV - Variables d'Environnement

Ce document décrit les variables d'environnement requises pour l'intégration Orange Money WebPay DEV (Sandbox Mali).

## Guide officiel
Documentation: https://developer.orange.com/apis/orange-money-webpay/

## Variables à ajouter dans votre fichier `.env`

```bash
# =============================================================================
# Orange Money WebPay DEV Configuration (Mali, Sandbox)
# =============================================================================
# Documentation: https://developer.orange.com/apis/orange-money-webpay/
# Guide officiel: Orange Money WebPay Dev (Mali)

# OAuth & API Configuration (section 2 du guide)
ORANGE_CLIENT_ID=your-orange-client-id-here
ORANGE_CLIENT_SECRET=your-orange-client-secret-here
ORANGE_APPLICATION_ID=your-orange-application-id-here

# OAuth Token URL (section 2 du guide)
# DEV/Sandbox: https://api.orange.com/oauth/v3/token
ORANGE_OAUTH_TOKEN_URL=https://api.orange.com/oauth/v3/token

# WebPay DEV URL (section 3 du guide)
# DEV/Sandbox: https://api.orange.com/orange-money-webpay/dev/v1/webpayment
# PROD: https://api.orange.com/orange-money-webpay/ml/v1/webpayment
ORANGE_WEBPAY_DEV_URL=https://api.orange.com/orange-money-webpay/dev/v1/webpayment

# Transaction Status URL (section 4 du guide)
# DEV/Sandbox: https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus
ORANGE_TRANSACTION_STATUS_URL=https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus

# Merchant Configuration
ORANGE_MERCHANT_KEY=your-orange-merchant-key-here
ORANGE_MERCHANT_MSISDN=your-merchant-msisdn-here
ORANGE_MERCHANT_AGENT_CODE=your-merchant-agent-code-here

# Callback URLs
# IMPORTANT: Orange Money n'accepte pas localhost/127.0.0.1 en production
# En sandbox, vous pouvez utiliser ngrok ou une URL publique de test
ORANGE_RETURN_URL=http://127.0.0.1:8000/payments/om/return/
ORANGE_CANCEL_URL=http://127.0.0.1:8000/payments/om/return/
ORANGE_NOTIFY_URL=http://127.0.0.1:8000/payments/om/notify/

# Test/Sandbox Configuration (section 6 du guide)
# Numéros de test fournis par Orange Money pour le sandbox
ORANGE_TEST_SUBSCRIBER_MSISDN=77011011234
ORANGE_TEST_SUBSCRIBER_PIN=4940

# Code pays pour les URLs Orange Money
# ml = Mali (default)
# ow = Guinée (Ouest)
# ci = Côte d'Ivoire
# sn = Sénégal
ORANGE_COUNTRY_CODE=ml

# URLs publiques pour le sandbox (optionnel)
# Si vous testez en local, configurez ngrok ou une URL publique de test
# OM_NGROK_URL=https://your-ngrok-url.ngrok.io
# OM_TEST_PUBLIC_URL=http://myvirtualshop.webnode.es
```

## Description des Variables

### OAuth & API

- **ORANGE_CLIENT_ID**: Identifiant client fourni par Orange Money Developer Portal
- **ORANGE_CLIENT_SECRET**: Secret client fourni par Orange Money Developer Portal
- **ORANGE_APPLICATION_ID**: ID de l'application Orange Money (optionnel selon version API)

### URLs API

- **ORANGE_OAUTH_TOKEN_URL**: Endpoint pour obtenir le token OAuth (section 2 du guide)
  - Default: `https://api.orange.com/oauth/v3/token`
  
- **ORANGE_WEBPAY_DEV_URL**: Endpoint pour initialiser un paiement WebPay (section 3 du guide)
  - Sandbox: `https://api.orange.com/orange-money-webpay/dev/v1/webpayment`
  - Production: `https://api.orange.com/orange-money-webpay/ml/v1/webpayment`

- **ORANGE_TRANSACTION_STATUS_URL**: Endpoint pour vérifier le statut d'une transaction (section 4 du guide)
  - Sandbox: `https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus`

### Merchant

- **ORANGE_MERCHANT_KEY**: Clé merchant fournie par Orange Money
- **ORANGE_MERCHANT_MSISDN**: Numéro MSISDN du merchant (format international)
- **ORANGE_MERCHANT_AGENT_CODE**: Code agent du merchant (si applicable)

### Callback URLs

- **ORANGE_RETURN_URL**: URL de retour après le paiement (return_url)
- **ORANGE_CANCEL_URL**: URL de retour si l'utilisateur annule (cancel_url)
- **ORANGE_NOTIFY_URL**: URL de notification webhook (notif_url)

⚠️ **IMPORTANT**: Orange Money n'accepte pas les URLs localhost/127.0.0.1 en production.
En sandbox, vous pouvez utiliser:
- ngrok: `https://your-app.ngrok.io`
- Une URL publique de test: `http://myvirtualshop.webnode.es` (exemple du guide)

### Test/Sandbox

- **ORANGE_TEST_SUBSCRIBER_MSISDN**: Numéro de test fourni par Orange (default: 77011011234)
- **ORANGE_TEST_SUBSCRIBER_PIN**: PIN de test fourni par Orange (default: 4940)
- **ORANGE_COUNTRY_CODE**: Code pays pour les URLs de paiement (default: ml)
  - `ml` = Mali
  - `ow` = Guinée (Ouest)
  - `ci` = Côte d'Ivoire
  - `sn` = Sénégal

## Comment Obtenir les Credentials

1. Créer un compte sur [Orange Developer Portal](https://developer.orange.com/)
2. Créer une application Orange Money WebPay
3. Récupérer le `client_id` et `client_secret` depuis le portail
4. Contacter Orange Money Mali pour obtenir le `merchant_key` et autres credentials merchant

## Tester l'Intégration

Une fois les variables configurées dans votre `.env`, testez l'intégration:

```bash
# Depuis le dossier auditshield/
python test_orange_money_sandbox.py
```

Ce script va:
1. Vérifier la configuration
2. Tester l'obtention du token OAuth
3. Tester l'initialisation d'un paiement WebPay
4. Afficher l'URL de paiement sandbox

## Flux de Paiement

1. Utilisateur clique sur "Payer avec Orange Money"
2. Application appelle `/store/buy/om/<slug>/`
3. Backend crée un Order et appelle l'API Orange Money
4. Utilisateur est redirigé vers `https://webpayment-ow-sb.orange-money.com/...`
5. Utilisateur entre son numéro et PIN
6. Orange Money envoie un webhook à `ORANGE_NOTIFY_URL`
7. Backend valide le paiement et envoie l'email de confirmation

## URLs du Projet

- **Checkout Orange Money**: `/store/buy/om/<product_slug>/`
- **Page de retour**: `/payments/om/return/`
- **Webhook**: `/payments/om/notify/`

## Notes de Sécurité

- Ne JAMAIS committer les credentials réels dans le code
- Utiliser uniquement les variables d'environnement
- En production, activer HTTPS pour tous les callbacks
- Valider les webhooks avec le `notif_token`

## Troubleshooting

### Erreur OAuth
- Vérifier `ORANGE_CLIENT_ID` et `ORANGE_CLIENT_SECRET`
- Vérifier que l'application est bien activée sur le portail Orange

### Erreur API WebPay
- Vérifier `ORANGE_MERCHANT_KEY`
- Vérifier que les URLs de callback sont valides (pas de localhost en prod)
- Vérifier les logs dans `logs/orange_money.log`

### Webhook non reçu
- Vérifier que `ORANGE_NOTIFY_URL` est accessible publiquement
- Utiliser ngrok pour tester en local
- Vérifier les logs du serveur web

## Support

Pour toute question sur l'intégration Orange Money WebPay:
- Documentation: https://developer.orange.com/apis/orange-money-webpay/
- Support Orange Money Mali: contact via le portail développeur

