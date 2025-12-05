# 📋 Implémentation Orange Money - Étapes et Références

## 🎯 Vue d'ensemble

Ce document détaille les étapes suivies pour implémenter l'intégration Orange Money WebPay Dev (Sandbox) dans AuditShield, ainsi que les outils et références utilisés.

---

## 📚 Références consultées

### 1. Documentation officielle Orange Money

| Document | Source | Utilisation |
|----------|--------|-------------|
| **guide_orange.md** | Guide officiel Orange Money WebPay Dev (PDF converti) | Référence principale pour l'API |
| **API Reference** | https://developer.orange.com/apis/om-webpay | Documentation en ligne |
| **Orange Developer Portal** | https://developer.orange.com/myapps | Gestion des applications et credentials |

### 2. Documentation du projet existant

| Document | Contenu |
|----------|---------|
| **orange_money_sandbox.md** | Guide de test sandbox (existant) |
| **ENV_TEMPLATE.txt** | Template des variables d'environnement |
| **store/services/orange_money.py** | Service API Orange Money (code source) |
| **store/views.py** | Vues Django existantes |
| **store/models.py** | Modèles Django (Order, Payment) |

### 3. Standards et patterns Django

- Django REST API patterns
- Django cache framework
- Django logging configuration
- Django views (function-based)
- Django URL routing

---

## 🛠️ Outils utilisés

### 1. Environnement de développement

| Outil | Version | Usage |
|-------|---------|-------|
| **Python** | 3.x | Langage principal |
| **Django** | 5.x | Framework web |
| **PostgreSQL** | - | Base de données |
| **Git** | - | Gestion de version |
| **VS Code** | - | Éditeur de code |

### 2. Bibliothèques Python

| Bibliothèque | Usage |
|--------------|-------|
| **requests** | Appels HTTP vers API Orange Money |
| **base64** | Encodage des credentials OAuth |
| **json** | Parsing des réponses API |
| **logging** | Logs structurés |
| **django.core.cache** | Cache du token OAuth |
| **django.core.exceptions** | Gestion des erreurs de configuration |

### 3. Outils de test

| Outil | Usage |
|-------|-------|
| **Django Management Commands** | Commandes de test (`test_orange_money_sandbox`) |
| **Python shell** | Tests manuels et débogage |
| **Postman** (potentiel) | Tests d'API |
| **Simulateur OTP Orange** | https://mpayment.orange-money.com/mpayment-otp/login |

### 4. Outils de documentation

| Outil | Usage |
|-------|-------|
| **Markdown** | Documentation technique |
| **ASCII diagrams** | Diagrammes de flux |
| **VS Code Markdown Preview** | Prévisualisation |

---

## 📝 Étapes d'implémentation

### Phase 1 : Analyse et configuration (Jour 1)

#### Étape 1.1 : Analyse de la documentation Orange Money
**Durée** : 2-3 heures

**Actions** :
- [x] Lecture du guide officiel Orange Money WebPay Dev (`guide_orange.md`)
- [x] Identification des endpoints API :
  - OAuth : `/oauth/v2/token`
  - WebPayment : `/orange-money-webpay/dev/v1/webpayment`
  - TransactionStatus : `/orange-money-webpay/dev/v1/transactionstatus`
- [x] Identification des credentials nécessaires :
  - `CLIENT_ID` et `CLIENT_SECRET` (OAuth)
  - `MERCHANT_KEY` (WebPay)
- [x] Analyse du flux de paiement complet

**Références** :
- `guide_orange.md` (sections 1-4)
- Guide officiel Orange (PDF)

---

#### Étape 1.2 : Configuration des variables d'environnement
**Durée** : 30 min

**Actions** :
- [x] Ajout des variables dans `ENV_TEMPLATE.txt` :
  ```bash
  OM_CLIENT_ID=
  OM_CLIENT_SECRET=
  OM_MERCHANT_KEY=
  OM_OAUTH_URL=https://api.orange.com/oauth/v2/token
  OM_WEBPAY_URL=https://api.orange.com/orange-money-webpay/dev/v1/webpayment
  OM_TRANSACTION_STATUS_URL=https://api.orange.com/orange-money-webpay/dev/v1/transactionstatus
  OM_RETURN_URL=http://127.0.0.1:8000/payments/om/return/
  OM_NOTIFY_URL=http://127.0.0.1:8000/payments/om/notify/
  OM_TEST_PUBLIC_URL=http://myvirtualshop.webnode.es
  ```
- [x] Configuration dans `.env` (local)

**Références** :
- `ENV_TEMPLATE.txt`
- `guide_orange.md` (section 1.2)

---

### Phase 2 : Implémentation du service API (Jour 1-2)

#### Étape 2.1 : Création du service orange_money.py
**Durée** : 4-5 heures

**Actions** :
- [x] Création de `store/services/orange_money.py`
- [x] Implémentation des exceptions personnalisées :
  ```python
  class OrangeMoneyError(Exception)
  class OrangeMoneyAuthError(OrangeMoneyError)
  class OrangeMoneyAPIError(OrangeMoneyError)
  ```
- [x] Implémentation de `_get_config()` :
  - Récupération des variables d'environnement
  - Validation des variables essentielles
  - Levée d'exception si manquantes

**Fichiers créés** :
- `store/services/orange_money.py` (ligne 1-70)

**Références** :
- Django `os.getenv()`
- Django `ImproperlyConfigured`

---

#### Étape 2.2 : Implémentation de l'authentification OAuth 2.0
**Durée** : 2-3 heures

**Actions** :
- [x] Implémentation de `get_access_token()` :
  - Vérification du cache Django
  - Encodage Basic Auth (base64)
  - POST vers `/oauth/v2/token`
  - Parsing de la réponse JSON
  - Mise en cache du token (90 jours - 1h)
  - Gestion des erreurs (401, 403, timeout, JSON invalide)
- [x] Configuration du cache :
  ```python
  _TOKEN_CACHE_KEY = "orange_money_access_token"
  _TOKEN_CACHE_TIMEOUT = 90 * 24 * 60 * 60  # 90 jours
  ```

**Fichiers modifiés** :
- `store/services/orange_money.py` (ligne 73-160)

**Références** :
- `guide_orange.md` (section 2 - OAuth)
- Django cache framework
- Python `base64.b64encode()`
- Python `requests.post()`

---

#### Étape 2.3 : Implémentation de la création de paiement
**Durée** : 4-5 heures

**Actions** :
- [x] Implémentation de `create_payment_request()` :
  - Récupération du token OAuth (via `get_access_token()`)
  - Construction du payload JSON selon le guide Orange :
    ```json
    {
      "merchant_key": "...",
      "currency": "OUV",  // Sandbox
      "order_id": "...",
      "amount": 15000,
      "return_url": "...",
      "cancel_url": "...",
      "notif_url": "...",
      "lang": "fr",
      "reference": "AuditShield"
    }
    ```
  - POST vers `/orange-money-webpay/dev/v1/webpayment`
  - Parsing de la réponse (status 201 attendu)
  - Extraction de `pay_token`, `payment_url`, `notif_token`
  - Reconstruction de l'URL sandbox correcte
  - Gestion des erreurs (400, 401, 403)
- [x] Gestion des URLs localhost :
  - Détection automatique de `localhost` / `127.0.0.1`
  - Remplacement par `OM_TEST_PUBLIC_URL` ou `OM_NGROK_URL`
  - Fallback vers URL de test par défaut

**Fichiers modifiés** :
- `store/services/orange_money.py` (ligne 162-407)

**Références** :
- `guide_orange.md` (section 3.1 - WebPayment)
- Django URL reverse
- Python `requests.post()`

---

#### Étape 2.4 : Implémentation de la vérification de statut
**Durée** : 1-2 heures

**Actions** :
- [x] Implémentation de `check_transaction_status()` :
  - Récupération du token OAuth
  - Construction du payload avec `order_id`, `amount`, `pay_token`
  - POST vers `/orange-money-webpay/dev/v1/transactionstatus`
  - Parsing de la réponse (status 201 attendu)
  - Extraction du statut et `txnid`
  - Gestion des erreurs réseau

**Fichiers modifiés** :
- `store/services/orange_money.py` (ligne 409-511)

**Références** :
- `guide_orange.md` (section 4 - TransactionStatus)

---

#### Étape 2.5 : Implémentation de la validation webhook
**Durée** : 1 heure

**Actions** :
- [x] Implémentation de `verify_webhook()` :
  - Parsing du payload JSON de la requête
  - Extraction de `status`, `notif_token`, `txnid`
  - Logging du webhook reçu
  - Gestion des erreurs de parsing
- [x] Implémentation de `map_provider_status_to_paid()` :
  - Mapping des statuts Orange Money vers PAID/FAILED
  - Liste des statuts valides : `["PAID", "SUCCESS", "COMPLETED", ...]`

**Fichiers modifiés** :
- `store/services/orange_money.py` (ligne 514-556)

**Références** :
- `guide_orange.md` (section 3.3 - Transaction Notification)

---

#### Étape 2.6 : Fonctions de compatibilité
**Durée** : 30 min

**Actions** :
- [x] Implémentation de `create_checkout()` :
  - Fonction de compatibilité pour les Kit complets
  - Récupération de l'Order via ClientInquiry
  - Appel à `create_payment_request()`
- [x] Implémentation de `check_transaction_status_legacy()` :
  - Fonction de compatibilité pour l'ancien code

**Fichiers modifiés** :
- `store/services/orange_money.py` (ligne 558-590)

**Références** :
- Code existant dans `store/views.py`

---

### Phase 3 : Implémentation des vues Django (Jour 2)

#### Étape 3.1 : Vue de création de paiement
**Durée** : 2 heures

**Actions** :
- [x] Création de `orange_start_payment()` dans `payment_views.py` :
  - Récupération du produit
  - Formulaire de collecte des informations client
  - Création de l'Order (status="PENDING")
  - Appel à `create_payment_request()`
  - Stockage du `notif_token` dans Order
  - Redirection vers `payment_url`
  - Gestion des erreurs avec messages Django

**Fichiers modifiés** :
- `store/payment_views.py`

**Références** :
- Django views
- Django forms
- Django messages framework

---

#### Étape 3.2 : Vue de retour utilisateur
**Durée** : 1 heure

**Actions** :
- [x] Création de `orange_return()` dans `payment_views.py` :
  - Récupération de l'Order via `order_id`
  - Affichage de la page "Paiement en cours"
  - **Important** : Ne valide PAS le paiement (seul le webhook valide)
  - Logging de la redirection

**Fichiers modifiés** :
- `store/payment_views.py`

**Références** :
- Django views
- Django templates

---

#### Étape 3.3 : Vue de webhook (notification)
**Durée** : 2-3 heures

**Actions** :
- [x] Création de `orange_notify()` dans `payment_views.py` :
  - Parsing du webhook via `verify_webhook()`
  - Récupération de l'Order via `notif_token`
  - Vérification de l'idempotence (Order déjà PAID ?)
  - Validation du `notif_token`
  - Si status="SUCCESS" :
    - `order.mark_paid()`
    - Création du `DownloadToken`
    - Envoi de l'email de confirmation
  - Réponse JSON `{"status": "ok"}`
  - Gestion des erreurs avec logs

**Fichiers modifiés** :
- `store/payment_views.py`

**Références** :
- `guide_orange.md` (section 3.3)
- Django views
- Django JsonResponse
- Django email

---

### Phase 4 : Configuration des URLs (Jour 2)

#### Étape 4.1 : Ajout des routes Orange Money
**Durée** : 30 min

**Actions** :
- [x] Ajout dans `store/urls.py` :
  ```python
  path("buy/om/<slug:product_slug>/", pay.orange_start_payment, name="orange_start"),
  path("payments/om/return/", pay.orange_return, name="orange_return"),
  path("payments/om/notify/", pay.orange_notify, name="orange_notify"),
  ```
- [x] Compatibilité avec les routes existantes

**Fichiers modifiés** :
- `store/urls.py`

**Références** :
- Django URL routing
- URLs existantes CinetPay

---

### Phase 5 : Templates et UI (Jour 2)

#### Étape 5.1 : Template de paiement en cours
**Durée** : 1 heure

**Actions** :
- [x] Création de `store/templates/store/payment_pending.html` :
  - Message "Paiement en cours de validation"
  - Instruction d'attendre l'email de confirmation
  - Lien vers l'accueil
  - Design cohérent avec le reste du site

**Fichiers créés** :
- `store/templates/store/payment_pending.html`

**Références** :
- Templates Django existants
- Bootstrap (si utilisé)

---

### Phase 6 : Logging et débogage (Jour 2-3)

#### Étape 6.1 : Implémentation du logging structuré
**Durée** : 1-2 heures

**Actions** :
- [x] Ajout de logs dans toutes les fonctions :
  - Format : `[OM][fonction] message | key1=value1 | key2=value2`
  - Niveaux : DEBUG, INFO, ERROR
  - Logs des requêtes/réponses API
  - Logs des webhooks
  - Logs des erreurs avec `exc_info=True`
- [x] Configuration du logger dans `settings/dev.py` :
  ```python
  LOGGING = {
      'loggers': {
          'store.services.orange_money': {
              'handlers': ['console'],
              'level': 'DEBUG',
          },
      },
  }
  ```

**Fichiers modifiés** :
- `store/services/orange_money.py` (tous les logs)
- `config/settings/dev.py` (configuration logging)

**Références** :
- Python logging module
- Django logging configuration

---

### Phase 7 : Tests et validation (Jour 3)

#### Étape 7.1 : Création de la commande de test
**Durée** : 2-3 heures

**Actions** :
- [x] Création de `store/management/commands/test_orange_money_sandbox.py` :
  - Commande Django pour tester l'intégration
  - Options :
    - `--amount` : Montant du paiement de test
    - `--check-status` : Vérifier le statut d'une transaction
    - `--pay-token` : Token pour vérification de statut
  - Affichage formaté des résultats
  - Gestion des erreurs

**Fichiers créés** :
- `store/management/commands/test_orange_money_sandbox.py`

**Références** :
- Django management commands
- Code de test similaire pour CinetPay

---

#### Étape 7.2 : Tests manuels
**Durée** : 2-3 heures

**Actions** :
- [x] Test OAuth :
  ```bash
  python manage.py shell
  >>> from store.services.orange_money import get_access_token
  >>> token = get_access_token()
  >>> print(token)
  ```
- [x] Test création de paiement :
  ```bash
  python manage.py test_orange_money_sandbox --amount 100
  ```
- [x] Test vérification de statut :
  ```bash
  python manage.py test_orange_money_sandbox \
    --check-status ORDER_ID --pay-token TOKEN
  ```
- [x] Vérification des logs

**Outils** :
- Django shell
- Commande de test personnalisée
- Logs Django

---

### Phase 8 : Documentation (Jour 3-4)

#### Étape 8.1 : Documentation technique
**Durée** : 4-5 heures

**Actions** :
- [x] Création de `orange_money_sandbox.md` :
  - Guide de test sandbox
  - Configuration des variables
  - Scénario de test complet
  - Dépannage
- [x] Mise à jour de `ENV_TEMPLATE.txt`
- [x] Commentaires dans le code

**Fichiers créés/modifiés** :
- `docs/orange_money_sandbox.md`
- `ENV_TEMPLATE.txt`
- `store/services/orange_money.py` (docstrings)

**Références** :
- Guide officiel Orange Money
- Documentation Django existante

---

#### Étape 8.2 : Documentation pour agents Orange
**Durée** : 6-8 heures

**Actions** :
- [x] Création de `PRESENTATION_ORANGE_MONEY_POUR_AGENTS.md` (15 pages) :
  - Contexte du projet
  - Architecture complète
  - Configuration détaillée
  - Flux de paiement avec diagrammes
  - Logging et débogage
  - Troubleshooting
  - Checklist d'intégration
- [x] Création de `PRESENTATION_RAPIDE_ORANGE_AGENTS.md` (8 pages) :
  - Présentation synthétique
  - Support de présentation
- [x] Création de `CONFIG_ORANGE_MONEY_RESUME.md` (12 pages) :
  - Configuration technique détaillée
  - Tous les payloads
  - Diagrammes de séquence
- [x] Création de `ORANGE_MONEY_QUICK_REF.md` (4 pages) :
  - Référence rapide
  - Aide-mémoire
- [x] Création de `EXEMPLE_TEST_ORANGE_MONEY.md` (10 pages) :
  - Trace complète avec logs
  - Scénario de bout en bout
- [x] Création de `INDEX_DOCUMENTATION_ORANGE_MONEY.md` :
  - Index de navigation
  - Parcours recommandés
- [x] Création de `README_PRESENTATION_ORANGE.md` :
  - Guide d'utilisation de la documentation

**Fichiers créés** :
- 7 fichiers de documentation (~60 pages au total)

**Outils** :
- Markdown
- ASCII diagrams
- Tableaux comparatifs

---

## 🔍 Défis rencontrés et solutions

### Défi 1 : URLs localhost non acceptées par Orange Money

**Problème** : Orange Money refuse les URLs contenant `localhost` ou `127.0.0.1`

**Solution implémentée** :
- Détection automatique de localhost dans les URLs
- Remplacement par `OM_TEST_PUBLIC_URL` (URL de test publique)
- Support de `OM_NGROK_URL` pour recevoir les webhooks en local
- Fallback automatique vers URL de test par défaut

**Code** :
```python
has_localhost = ("localhost" in return_url.lower() or "127.0.0.1" in return_url.lower())
if has_localhost:
    if test_public_url:
        return_url = test_public_url + reverse("store:orange_return")
    elif ngrok_url:
        notify_url = ngrok_url + reverse("store:orange_notify")
```

---

### Défi 2 : URL sandbox différente de l'URL retournée par l'API

**Problème** : L'API retourne parfois une URL `webpayment-qualif` au lieu de `webpayment-ow-sb`

**Solution implémentée** :
- Détection du mode sandbox (URL contient `/dev/v1/`)
- Reconstruction de l'URL sandbox correcte avec le domaine `webpayment-ow-sb`
- Logging de l'URL originale et corrigée

**Code** :
```python
if "/dev/v1/webpayment" in webpay_url:
    sandbox_payment_url = f"https://webpayment-ow-sb.orange-money.com/payment/pay_token/{pay_token}"
    payment_url = sandbox_payment_url
```

---

### Défi 3 : Cache du token OAuth

**Problème** : Éviter de refaire l'authentification OAuth à chaque requête

**Solution implémentée** :
- Utilisation du cache Django
- Durée de vie : 90 jours (selon le guide Orange)
- Expiration anticipée de 1h pour éviter les erreurs
- Clé de cache unique : `orange_money_access_token`

**Code** :
```python
cached_token = cache.get(_TOKEN_CACHE_KEY)
if cached_token:
    return cached_token

# ... obtenir nouveau token ...

cache_timeout = min(expires_in - 3600, _TOKEN_CACHE_TIMEOUT)
cache.set(_TOKEN_CACHE_KEY, access_token, cache_timeout)
```

---

### Défi 4 : Validation du webhook

**Problème** : Comment s'assurer que le webhook provient bien d'Orange Money

**Solution implémentée** :
- Vérification du `notif_token` (retourné lors de la création du paiement)
- Stockage du `notif_token` dans l'Order
- Comparaison du `notif_token` reçu avec celui stocké
- Idempotence : vérification si Order déjà PAID

**Code** :
```python
if webhook["notif_token"] != order.notif_token:
    logger.error("notif_token mismatch")
    return JsonResponse({"error": "Invalid notif_token"}, status=403)

if order.status == "PAID":
    logger.info("Order déjà payé, ignorer webhook")
    return JsonResponse({"status": "ok"})
```

---

## 📊 Métriques du projet

### Code produit

| Fichier | Lignes | Fonctions | Description |
|---------|--------|-----------|-------------|
| `store/services/orange_money.py` | ~590 | 9 | Service API principal |
| `store/payment_views.py` (ajouts) | ~200 | 3 | Vues Django |
| `store/urls.py` (ajouts) | ~10 | - | Configuration URLs |
| `store/management/commands/test_orange_money_sandbox.py` | ~150 | 1 | Commande de test |
| **Total** | **~950** | **13** | **Code Python** |

### Documentation produite

| Type | Fichiers | Pages | Mots estimés |
|------|----------|-------|--------------|
| Documentation agents Orange | 7 | ~60 | ~30,000 |
| Documentation technique | 2 | ~15 | ~7,500 |
| Code comments & docstrings | - | - | ~5,000 |
| **Total** | **9** | **~75** | **~42,500** |

### Temps estimé

| Phase | Durée |
|-------|-------|
| Analyse et configuration | 3-4 heures |
| Implémentation service API | 12-15 heures |
| Implémentation vues Django | 5-6 heures |
| Configuration URLs et templates | 2-3 heures |
| Logging et débogage | 2-3 heures |
| Tests et validation | 4-5 heures |
| Documentation | 10-13 heures |
| **Total** | **38-49 heures** (~1 semaine) |

---

## ✅ Checklist d'implémentation

### Configuration
- [x] Variables d'environnement ajoutées dans `ENV_TEMPLATE.txt`
- [x] Variables configurées dans `.env` (local)
- [x] Credentials obtenus depuis Orange Developer Portal

### Service API
- [x] Exceptions personnalisées créées
- [x] Fonction `_get_config()` implémentée
- [x] Fonction `get_access_token()` implémentée (OAuth)
- [x] Fonction `create_payment_request()` implémentée (WebPay)
- [x] Fonction `check_transaction_status()` implémentée
- [x] Fonction `verify_webhook()` implémentée
- [x] Fonction `map_provider_status_to_paid()` implémentée
- [x] Fonctions de compatibilité implémentées
- [x] Gestion des URLs localhost implémentée

### Vues Django
- [x] Vue `orange_start_payment()` implémentée
- [x] Vue `orange_return()` implémentée
- [x] Vue `orange_notify()` implémentée
- [x] Gestion des erreurs avec messages Django

### URLs et templates
- [x] Routes ajoutées dans `store/urls.py`
- [x] Template `payment_pending.html` créé

### Logging
- [x] Logging structuré implémenté
- [x] Configuration du logger dans `settings/dev.py`
- [x] Logs de toutes les étapes

### Tests
- [x] Commande de test créée
- [x] Tests manuels effectués
- [x] Logs vérifiés

### Documentation
- [x] Documentation technique créée
- [x] Documentation pour agents Orange créée (7 documents)
- [x] Guide d'utilisation créé
- [x] Code commenté et documenté

---

## 🚀 Prochaines étapes

### Court terme (avec agents Orange)
- [ ] Validation de la configuration actuelle
- [ ] Obtention des identifiants de test complets
- [ ] Test E2E avec Simulateur OTP
- [ ] Validation du format webhook réel

### Moyen terme (passage en production)
- [ ] Obtention des identifiants de production
- [ ] Changement des endpoints (`/dev/v1/` → `/v1/`)
- [ ] Changement de la devise (`OUV` → `XOF`)
- [ ] Configuration des URLs HTTPS publiques
- [ ] Tests en environnement de production

### Long terme (améliorations)
- [ ] Monitoring des transactions
- [ ] Dashboard d'administration
- [ ] Rapports de paiement
- [ ] Optimisation des performances

---

## 📞 Ressources et contacts

### Orange Money
- **Simulateur OTP** : https://mpayment.orange-money.com/mpayment-otp/login
- **Developer Portal** : https://developer.orange.com/myapps
- **Support** : georgiana.cruceru@orange.com

### Documentation
- **Guide officiel** : `auditshield/guide_orange.md`
- **Documentation complète** : `auditshield/docs/`
- **Code source** : `auditshield/store/services/orange_money.py`

---

**Document d'implémentation** - Orange Money WebPay Dev  
**Projet** : AuditShield  
**Date** : 4 décembre 2024  
**Version** : 1.0.0  
**Statut** : ✅ Implémentation complète (Sandbox)

