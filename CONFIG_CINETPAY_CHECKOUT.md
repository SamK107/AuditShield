# Configuration CinetPay - Analyse du Checkout

## Problème identifié

Quand vous cliquez sur **"Payer avec CinetPay"** sur `http://127.0.0.1:8000/kit/inquiry/34/checkout/`, vous êtes redirigé directement vers la page de remerciement au lieu de passer par le checkout de CinetPay.

## Configurations existantes

### 1. Variables d'environnement (fichier `.env` ou cPanel)

Les variables suivantes sont utilisées par le système :

```env
# URL de l'API CinetPay
CINETPAY_API_URL=https://api-checkout.cinetpay.com

# Identifiants CinetPay (OBLIGATOIRES pour le mode production)
CINETPAY_API_KEY=votre_clé_api
CINETPAY_SITE_ID=votre_site_id

# URLs de retour (optionnelles, avec fallback dynamique)
CINETPAY_RETURN_URL=http://127.0.0.1:8000/payments/cinetpay/return/
CINETPAY_NOTIFY_URL=http://127.0.0.1:8000/payments/cinetpay/notify/

# Mode d'environnement (sandbox ou production)
CINETPAY_ENV=sandbox

# Canaux de paiement
CINETPAY_CHANNELS=CREDIT_CARD

# ⚠️ MODE MOCK (DÉSACTIVEZ EN PRODUCTION)
CINETPAY_MOCK=0  # Mettre à 0 ou ne pas définir pour utiliser l'API réelle
```

### 2. Configuration dans `config/settings/base.py`

```python
# Lignes 183-189
CINETPAY_SITE_ID = env.str("CINETPAY_SITE_ID", default=None)
CINETPAY_API_KEY = env.str("CINETPAY_API_KEY", default=None)
CINETPAY_SECRET_KEY = env.str("CINETPAY_SECRET_KEY", default=None)
CINETPAY_MODE = env.str("CINETPAY_MODE", "PROD").upper()
CINETPAY_ENV = env.str("CINETPAY_ENV", "sandbox")
CINETPAY_MOCK = os.getenv("CINETPAY_MOCK", "0") == "1"  # ⚠️ Mode mock
```

### 3. Flux de paiement actuel

#### Étape 1 : Formulaire de checkout (`kit_checkout`)
**Fichier :** `store/views.py` (lignes 380-505)

Quand l'utilisateur soumet le formulaire avec "Payer avec CinetPay" :
1. Une `Order` est créée avec un `provider_ref` unique
2. `cinetpay.init_payment_auto(order, request)` est appelé
3. Cette fonction retourne une URL de redirection

#### Étape 2 : Initialisation du paiement (`init_payment_auto`)
**Fichier :** `store/services/cinetpay.py` (lignes 505-547)

**Comportement selon le mode :**

**Mode MOCK (si `CINETPAY_MOCK=1`) :**
- Retourne : `/payments/cinetpay/mock/?transaction_id=...`
- ⚠️ **PROBLÈME** : Cette URL redirige immédiatement vers la page de retour, sautant le checkout

**Mode PRODUCTION (si `CINETPAY_MOCK=0` ou non défini) :**
- Vérifie que `CINETPAY_API_KEY` et `CINETPAY_SITE_ID` sont configurés
- Appelle l'API CinetPay réelle (`/v2/payment`)
- Retourne l'URL de checkout CinetPay (`payment_url`)

#### Étape 3 : Checkout CinetPay

**En mode PRODUCTION :**
- L'utilisateur est redirigé vers `https://secure.cinetpay.com/...` (URL fournie par CinetPay)
- L'utilisateur paie sur la plateforme CinetPay
- Après paiement, CinetPay redirige vers `CINETPAY_RETURN_URL`

**En mode MOCK :**
- L'utilisateur est redirigé vers `/payments/cinetpay/mock/`
- Cette page redirige immédiatement vers `/payments/cinetpay/return/?transaction_id=...`
- ⚠️ **C'est pourquoi vous voyez directement la page de remerciement**

#### Étape 4 : Retour après paiement (`cinetpay_return`)
**Fichier :** `store/views.py` (lignes 1244-1301)

1. Récupère le `transaction_id` depuis les paramètres GET/POST
2. Trouve l'`Order` correspondante
3. Vérifie le statut du paiement via `cinetpay.payment_check()`
4. Si payé, marque la commande comme payée
5. Pour les kits : redirige vers `kit_payment_success` (page de remerciement)
6. Pour les ebooks : redirige vers la page de téléchargement

#### Étape 5 : Webhook (`cinetpay_notify`)
**Fichier :** `store/views.py` (lignes 1309-1343)

- CinetPay envoie une notification serveur-à-serveur
- Vérifie la signature HMAC
- Marque la commande comme payée si le statut est valide

## Causes possibles du problème

### 1. Mode MOCK activé ⚠️ (PROBABLE)

Si `CINETPAY_MOCK=1` est défini dans votre `.env`, le système utilise le mode mock qui saute le checkout.

**Solution :**
```env
# Dans votre fichier .env
CINETPAY_MOCK=0
# OU supprimez complètement cette ligne
```

### 2. Clés API manquantes ou incorrectes

Si `CINETPAY_API_KEY` ou `CINETPAY_SITE_ID` ne sont pas configurés, le système peut :
- Lever une exception (visible dans les logs)
- Ou utiliser le mode mock par défaut

**Solution :**
```env
# Vérifiez que ces variables sont définies avec vos vraies clés
CINETPAY_API_KEY=votre_vraie_clé_api
CINETPAY_SITE_ID=votre_vrai_site_id
```

### 3. Erreur lors de l'appel API

Si l'appel à l'API CinetPay échoue, une exception est levée et un message d'erreur est affiché.

**Vérification :**
- Consultez les logs Django pour voir les erreurs
- Vérifiez que `CINETPAY_API_URL` est correct
- Vérifiez que vous êtes en mode `sandbox` ou `production` selon vos clés

## Configuration recommandée pour la production

```env
# Mode PRODUCTION
CINETPAY_MOCK=0
CINETPAY_ENV=production
CINETPAY_API_URL=https://api-checkout.cinetpay.com
CINETPAY_API_KEY=votre_clé_api_production
CINETPAY_SITE_ID=votre_site_id_production

# URLs de retour (utilisez votre domaine réel)
CINETPAY_RETURN_URL=https://votre-domaine.com/payments/cinetpay/return/
CINETPAY_NOTIFY_URL=https://votre-domaine.com/payments/cinetpay/notify/
```

## Vérification rapide

Pour vérifier votre configuration actuelle, exécutez dans le shell Django :

```python
import os
print("CINETPAY_MOCK:", os.getenv("CINETPAY_MOCK", "0"))
print("CINETPAY_API_KEY:", "présente" if os.getenv("CINETPAY_API_KEY") else "MANQUANTE")
print("CINETPAY_SITE_ID:", "présent" if os.getenv("CINETPAY_SITE_ID") else "MANQUANT")
print("CINETPAY_API_URL:", os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com"))
```

## Fichiers clés à examiner

1. **`store/services/cinetpay.py`** : Logique d'appel API et mode mock
2. **`store/views.py`** : 
   - `kit_checkout` (ligne 380) : Formulaire de checkout
   - `cinetpay_return` (ligne 1244) : Retour après paiement
   - `cinetpay_notify` (ligne 1309) : Webhook
3. **`store/payment_views.py`** : 
   - `cinetpay_mock_checkout` (ligne 204) : Page mock qui redirige directement
4. **`config/settings/base.py`** : Configuration Django

## Flux attendu (mode production)

1. ✅ Utilisateur clique sur "Payer avec CinetPay"
2. ✅ Formulaire soumis → `Order` créée
3. ✅ `init_payment_auto()` appelle l'API CinetPay
4. ✅ Redirection vers `https://secure.cinetpay.com/...` (checkout CinetPay)
5. ✅ Utilisateur paie sur CinetPay
6. ✅ CinetPay redirige vers `/payments/cinetpay/return/`
7. ✅ Webhook CinetPay notifie `/payments/cinetpay/notify/`
8. ✅ Commande marquée comme payée
9. ✅ Redirection vers la page de remerciement

## Action immédiate

**Vérifiez votre fichier `.env` et assurez-vous que :**
1. `CINETPAY_MOCK=0` (ou la ligne est absente)
2. `CINETPAY_API_KEY` et `CINETPAY_SITE_ID` sont définis avec vos vraies clés
3. Redémarrez votre serveur Django après modification

