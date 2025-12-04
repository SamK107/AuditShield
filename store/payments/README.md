# Architecture des Paiements - AuditShield

## Analyse de l'Existant

### Modèles de Commande

1. **`Order`** (`store/models.py`)
   - Modèle principal pour les commandes (ebook, produits)
   - Champs clés :
     - `status` : CREATED, PENDING, PAID, FAILED, CANCELED
     - `provider_ref` : référence unique du provider (CinetPay ou Orange Money)
     - `cinetpay_payment_id` : ID transaction CinetPay (legacy)
     - `amount_fcfa` : montant en FCFA
     - `currency` : XOF par défaut
   - Méthode `mark_paid()` : marque la commande comme payée et déclenche le fulfillment

2. **`ClientInquiry`** (`store/models.py`)
   - Pour les demandes de Kit complet personnalisé
   - Relation avec `Order` via `order` (ForeignKey)
   - Champs : `payment_status`, `processing_state`, `estimated_price_fcfa`

3. **`Payment`** (`store/models.py`)
   - Modèle générique pour les paiements CinetPay (legacy)
   - Champs : `order_id`, `provider_tx_id`, `status`, `amount`, `currency`

4. **`PaymentIntent`** (`store/models.py`)
   - Pour les intentions de paiement (Kit complet)
   - Supporte plusieurs providers : `cinetpay`, `om` (Orange Money)
   - Relation avec `ClientInquiry`

### Implémentation CinetPay

**Fichiers principaux :**
- `store/services/cinetpay.py` : Service complet avec :
  - `init_payment()` : Initie un paiement
  - `init_payment_auto()` : Wrapper haut niveau pour Order
  - `check_transaction()` : Vérifie le statut d'une transaction
  - `verify_signature()` : Vérifie la signature HMAC des webhooks
  - Mode mock activable via `CINETPAY_MOCK=1`

**Vues :**
- `store/views.py` : `cinetpay_return()`, `cinetpay_notify()`
- `store/payment_views.py` : `start_checkout()` (unifié CinetPay/Orange Money)

**URLs :**
- `/payments/cinetpay/return/` : Retour après paiement
- `/payments/cinetpay/notify/` : Webhook serveur-à-serveur

### Implémentation Orange Money (Existant - Incomplet)

**Fichiers existants :**
- `store/services/orange_money.py` : Service basique avec :
  - `create_sandbox_payment_request()` : Crée une demande de paiement
  - `check_payment_status()` : Vérifie le statut
  - `verify_webhook()` : Vérifie la signature webhook
  - `map_provider_status_to_paid()` : Mappe les statuts

**Problèmes identifiés :**
1. Pas de modèle dédié `OrangeMoneyPayment` pour tracer les transactions
2. Pas d'implémentation OAuth pour obtenir le `access_token`
3. Configuration incomplète (manque CLIENT_ID, CLIENT_SECRET, etc.)
4. Pas de gestion propre des erreurs métier
5. Pas de logs structurés pour les transactions
6. Pas de commande de management pour simuler les paiements

## Architecture Proposée

### Structure Modulaire

```
store/
├── payments/
│   ├── __init__.py
│   ├── README.md (ce fichier)
│   ├── orange_money/
│   │   ├── __init__.py
│   │   ├── api.py          # Client API Orange Money (OAuth, initiate_payment)
│   │   ├── models.py        # OrangeMoneyPayment, OrangeMoneyPaymentLog
│   │   ├── views.py         # start, notify, success, failed
│   │   ├── urls.py          # Routes Orange Money
│   │   └── exceptions.py    # OrangeMoneyError, OrangeMoneyAuthError, etc.
│   └── providers.py         # BasePaymentProvider (pattern abstrait)
```

### Pattern Provider (Optionnel - pour extensibilité future)

```python
# BasePaymentProvider (abstrait)
class BasePaymentProvider:
    def initiate_payment(self, order, request) -> str:  # URL de redirection
        raise NotImplementedError
    
    def verify_webhook(self, request) -> dict:
        raise NotImplementedError
    
    def check_status(self, reference: str) -> dict:
        raise NotImplementedError

# Implémentations
class CinetpayPaymentProvider(BasePaymentProvider):
    ...

class OrangeMoneyPaymentProvider(BasePaymentProvider):
    ...
```

**Note :** Pour l'instant, on garde les services séparés (`cinetpay.py`, `orange_money.py`) pour ne pas casser l'existant. Le pattern provider peut être introduit plus tard si besoin.

### Flux de Paiement Orange Money

1. **Initiation** (`start_orange_payment`)
   - Utilisateur clique sur "Payer avec Orange Money"
   - Création d'un `OrangeMoneyPayment` (status=INITIATED)
   - Appel API : OAuth → `get_access_token()`
   - Appel API : `initiate_payment()` → obtient `payment_url` ou flow STK push
   - Redirection vers `payment_url` OU affichage page "En attente de validation"

2. **Callback/Webhook** (`orange_payment_notify`)
   - Orange Money appelle `/payments/orange/notify/`
   - Vérification signature (si disponible)
   - Mise à jour `OrangeMoneyPayment` (status, callback_payload)
   - Si status=SUCCESS → `order.mark_paid()` + fulfillment

3. **Retour Utilisateur** (`orange_payment_success` / `orange_payment_failed`)
   - Utilisateur redirigé après paiement
   - Affichage page de confirmation ou d'échec
   - Si callback en retard, informer que le traitement est en cours

### Modèles de Données

**OrangeMoneyPayment :**
- `reference` : référence interne unique (ex: "OM-{uuid}")
- `external_transaction_id` : ID transaction Orange Money
- `status` : INITIATED, PENDING, SUCCESS, FAILED, CANCELLED, ERROR
- `amount`, `currency` : montant et devise
- `customer_msisdn` : numéro téléphone client
- `raw_request_payload`, `raw_response_payload` : JSON pour traçabilité
- `callback_payload` : payload du webhook
- Relation : `GenericForeignKey` vers Order ou ClientInquiry

**OrangeMoneyPaymentLog :**
- `payment` : FK vers OrangeMoneyPayment
- `event_type` : INIT, CALLBACK, RETRY, ERROR, etc.
- `payload` : JSON de l'événement
- `created_at` : timestamp

### Configuration

**Variables d'environnement requises (.env) :**
```
# Orange Money Mali (Sandbox)
OM_CLIENT_ID=...
OM_CLIENT_SECRET=...
OM_MERCHANT_ID=...
OM_MERCHANT_KEY=...
OM_MSISDN_TEST=77011011234
OM_API_BASE_URL=https://api.orange.com
OM_COLLECT_URL=https://api.orange.com/orange-money-webpay/ml/v1/transaction/init
OM_CALLBACK_URL=http://127.0.0.1:8000/payments/orange/notify/
OM_RETURN_URL_SUCCESS=http://127.0.0.1:8000/payments/orange/success/
OM_RETURN_URL_FAILED=http://127.0.0.1:8000/payments/orange/failed/
```

**Settings Django :**
- Structure `ORANGE_MONEY_CONFIG` dans `config/settings/base.py`
- Validation au démarrage si variables manquantes (en prod)

### Tests & Simulation Sandbox

**Commande de management :**
```bash
python manage.py simulate_orange_payment_success <reference>
```

Simule un callback "success" pour tester le pipeline complet sans appel API réel.

---

**Date de création :** 2025-01-XX
**Auteur :** Assistant Django Expert

