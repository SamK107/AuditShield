# Logging Orange Money WebPay Dev

## Vue d'ensemble

Ce document décrit le système de logging détaillé pour l'intégration Orange Money WebPay Dev dans AUDITSHIELD.

## Configuration

### Fichiers modifiés

1. **`store/services/orange_money.py`** : Service Orange Money avec logging détaillé
2. **`config/settings/base.py`** : Configuration Django LOGGING
3. **`store/payment_views.py`** : Vues de paiement avec gestion d'erreurs améliorée

### Structure des logs

Les logs Orange Money sont écrits dans :
- **Console** : Tous les logs niveau INFO et supérieur
- **Fichier** : `logs/orange_money.log` (création automatique)

## Format des logs

### Format général

```
[{levelname}] {asctime} {name} | {message}
```

Exemple :
```
[INFO] 2025-12-05 10:30:45 store.services.orange_money | ORANGE_WEBPAY_REQUEST | OAuth Token | url=https://api.orange.com/oauth/v2/token | headers={...} | body={...}
```

### Logs de requêtes (REQUEST)

Pour chaque appel API Orange Money, un log `ORANGE_WEBPAY_REQUEST` est créé avec :

```
ORANGE_WEBPAY_REQUEST | <Type> | url=<url_endpoint> | headers=<headers_masqués> | body=<payload_json>
```

**Types de requêtes :**
- `OAuth Token` : Authentification OAuth2
- `WebPayment Init` : Initialisation de paiement
- `Transaction Status` : Vérification de statut

**Masquage des données sensibles :**
- `Authorization: Bearer ***masked***` : Token OAuth masqué
- `merchant_key: "abc1***masked***"` : Clé merchant masquée (4 premiers caractères visibles)
- Tous les champs contenant "token", "secret", "key", "password", "auth" sont masqués

### Logs de réponses (RESPONSE)

Pour chaque réponse de l'API Orange Money :

```
ORANGE_WEBPAY_RESPONSE | <Type> | status=<http_status> | body=<response_json>
```

**Contenu :**
- `status` : Code HTTP de la réponse (attendu : 200 pour OAuth, 201 pour WebPayment)
- `body` : Réponse JSON complète avec tokens masqués

### Logs d'erreurs

En cas d'erreur API (status != 201 pour WebPayment) :

```
[ERROR] 2025-12-05 10:30:45 store.services.orange_money | [OM][create_payment] HTTP 400 (attendu 201): {...}
```

Suivi de logs détaillés dans `payment_views.py` :

```
[ERROR] 2025-12-05 10:30:45 store.payment_views | [OM][start_checkout] Erreur API (status=400): ...
[ERROR] 2025-12-05 10:30:45 store.payment_views | [OM][start_checkout] Response data: {...}
```

## Fonctions de masquage

### `_mask_sensitive_data(data: dict, keys_to_mask: list) -> dict`

Masque les valeurs des clés sensibles dans un dictionnaire.

**Clés masquées par défaut :**
- `token`
- `secret`
- `key`
- `password`
- `auth`

**Stratégie de masquage :**
- Garde les 4 premiers caractères pour debug : `"abc1***masked***"`
- Si < 4 caractères : `"***masked***"`

### `_mask_authorization_header(headers: dict) -> dict`

Masque le header `Authorization` pour le logging.

**Exemple :**
```python
# Avant
{"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}

# Après
{"Authorization": "Bearer ***masked***"}
```

## Exemples de logs

### 1. Authentification OAuth réussie

```
[INFO] 2025-12-05 10:30:45 store.services.orange_money | ORANGE_WEBPAY_REQUEST | OAuth Token | url=https://api.orange.com/oauth/v2/token | headers={"Authorization": "Basic ***masked***", "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"} | body={"grant_type": "client_credentials"}

[INFO] 2025-12-05 10:30:46 store.services.orange_money | ORANGE_WEBPAY_RESPONSE | OAuth Token | status=200 | body={"access_token": "eyJh***masked***", "token_type": "Bearer", "expires_in": 7776000}

[INFO] 2025-12-05 10:30:46 store.services.orange_money | [OM][OAuth] Token obtenu avec succès (cache pour 7772400s)
```

### 2. Initialisation de paiement réussie

```
[INFO] 2025-12-05 10:31:00 store.services.orange_money | ORANGE_WEBPAY_REQUEST | WebPayment Init | url=https://api.orange.com/orange-money-webpay/dev/v1/webpayment | headers={"Authorization": "Bearer ***masked***", "Content-Type": "application/json", "Accept": "application/json"} | body={"merchant_key": "abc1***masked***", "currency": "OUV", "order_id": "a1b2c3d4", "amount": 5000, "return_url": "http://example.com/return", "cancel_url": "http://example.com/return", "notif_url": "http://example.com/notify", "lang": "fr", "reference": "AuditShield"}

[INFO] 2025-12-05 10:31:01 store.services.orange_money | ORANGE_WEBPAY_RESPONSE | WebPayment Init | status=201 | body={
  "status": "SUCCESS",
  "message": "OK",
  "pay_token": "dd49***masked***",
  "notif_token": "e8f1***masked***",
  "payment_url": "https://webpayment-ow-sb.orange-money.com/payment/pay_token/dd497bda..."
}

[INFO] 2025-12-05 10:31:01 store.services.orange_money | [OM][create_payment] Payment créé avec succès | payment_url=https://webpayment-ow-sb.orange-money.com/payment/pay_token/dd497bda... | pay_token=dd497bda3b250e536186... | notif_token=e8f1a2b3c4d5e6f7...
```

### 3. Erreur API (status != 201)

```
[INFO] 2025-12-05 10:32:00 store.services.orange_money | ORANGE_WEBPAY_REQUEST | WebPayment Init | url=https://api.orange.com/orange-money-webpay/dev/v1/webpayment | headers={"Authorization": "Bearer ***masked***", "Content-Type": "application/json", "Accept": "application/json"} | body={"merchant_key": "abc1***masked***", "currency": "OUV", "order_id": "a1b2c3d4", "amount": 5000, ...}

[INFO] 2025-12-05 10:32:01 store.services.orange_money | ORANGE_WEBPAY_RESPONSE | WebPayment Init | status=400 | body={"error": "invalid_merchant_key", "error_description": "Merchant key is invalid"}

[ERROR] 2025-12-05 10:32:01 store.services.orange_money | [OM][create_payment] HTTP 400 (attendu 201): {'error': 'invalid_merchant_key', 'error_description': 'Merchant key is invalid'}

[ERROR] 2025-12-05 10:32:01 store.payment_views | [OM][start_checkout] Erreur API (status=400): Erreur API Orange Money 400 (attendu 201)

[ERROR] 2025-12-05 10:32:01 store.payment_views | [OM][start_checkout] Response data: {"error": "invalid_merchant_key", "error_description": "Merchant key is invalid"}
```

## Utilisation pour le débogage

### Consulter les logs

```bash
# Logs en temps réel
tail -f logs/orange_money.log

# Filtrer les requêtes
grep "ORANGE_WEBPAY_REQUEST" logs/orange_money.log

# Filtrer les réponses
grep "ORANGE_WEBPAY_RESPONSE" logs/orange_money.log

# Filtrer les erreurs
grep "ERROR" logs/orange_money.log
```

### Analyser une transaction

Pour tracer une transaction complète, rechercher par `order_id` :

```bash
grep "a1b2c3d4" logs/orange_money.log
```

### Vérifier les status codes

```bash
# Voir tous les status codes retournés par l'API
grep "ORANGE_WEBPAY_RESPONSE" logs/orange_money.log | grep -oP "status=\d+"
```

## Sécurité

### Données masquées

Les données suivantes sont **toujours masquées** dans les logs :

- Token OAuth (Bearer token)
- Clé merchant (merchant_key)
- Tokens de paiement (pay_token, notif_token)
- Secrets client (client_secret)
- Credentials Basic Auth

### Données non masquées (safe)

- URL d'endpoint
- HTTP status code
- order_id
- amount
- currency
- Timestamps
- Messages d'erreur (sans secrets)

### Conformité

- ✅ Aucun token complet dans les logs
- ✅ Clés API masquées (4 premiers caractères visibles pour debug)
- ✅ Headers Authorization masqués
- ✅ Logs stockés localement (non versionnés)
- ✅ Fichier `logs/*.log` exclu via `.gitignore`

## Configuration avancée

### Changer le niveau de logging

Dans `config/settings/base.py` :

```python
"loggers": {
    "store.services.orange_money": {
        "handlers": ["console", "orange_money_file"],
        "level": "DEBUG",  # INFO par défaut, DEBUG pour plus de détails
        "propagate": False,
    },
}
```

### Rotation des logs

Pour éviter que `orange_money.log` ne devienne trop gros, utiliser `RotatingFileHandler` :

```python
"orange_money_file": {
    "class": "logging.handlers.RotatingFileHandler",
    "filename": str(LOGS_DIR / "orange_money.log"),
    "formatter": "verbose",
    "level": "INFO",
    "encoding": "utf-8",
    "maxBytes": 10 * 1024 * 1024,  # 10 MB
    "backupCount": 5,  # Garder 5 fichiers de backup
},
```

## Troubleshooting

### Les logs ne s'écrivent pas dans le fichier

1. Vérifier que le dossier `logs/` existe :
   ```bash
   mkdir -p logs
   ```

2. Vérifier les permissions :
   ```bash
   chmod 755 logs
   ```

3. Vérifier la configuration dans `base.py` :
   ```python
   LOGS_DIR = BASE_DIR / "logs"
   LOGS_DIR.mkdir(exist_ok=True)
   ```

### Les tokens ne sont pas masqués

Vérifier que `_mask_sensitive_data()` et `_mask_authorization_header()` sont bien appelées avant chaque log de requête/réponse.

### Logs trop verbeux

Réduire le niveau à `WARNING` ou `ERROR` :

```python
"level": "WARNING",  # N'affichera que warnings et erreurs
```

## Références

- Guide Orange Money WebPay Dev (PDF officiel)
- Django Logging Documentation : https://docs.djangoproject.com/en/5.0/topics/logging/
- Python logging : https://docs.python.org/3/library/logging.html

