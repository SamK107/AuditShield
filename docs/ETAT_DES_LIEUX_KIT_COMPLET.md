# 📊 ÉTAT DES LIEUX — KIT COMPLET DE PRÉPARATION À L'AUDIT

## 🎯 CONTEXTE

**Objectif final** : Implémenter un workflow complet pour le Kit Complet de Préparation à l'Audit avec :
1. Soumission d'un formulaire par le client
2. Génération automatique d'un document Word par l'IA (basé sur `kit_complet_consigne.md`)
3. Traitement et validation par un humain (upload PDF)
4. **Conditionnement à un paiement** avant envoi du lien sécurisé au client

**URL actuelle de traitement** : `http://127.0.0.1:8000/kit-complet-traitement/`

---

## ✅ CE QUI EXISTE ACTUELLEMENT

### 1. **MODÈLES DE DONNÉES**

#### `ClientInquiry` (store/models.py:275)
- **Type** : `KIND_KIT` pour les demandes de kit complet
- **Champs principaux** :
  - Informations client : `contact_name`, `email`, `phone`
  - Informations organisation : `organization_name`, `statut_juridique`, `location`, `sector`, etc.
  - **Statut IA** : `ai_status` (PENDING, DONE, ERROR)
  - **Fichiers** :
    - `ai_doc` : Document Word généré par l'IA (stocké dans `PRIVATE_MEDIA_ROOT/kits/ai/`)
    - `human_pdf` : PDF final validé par humain (stocké dans `PRIVATE_MEDIA_ROOT/kits/pdf/`)
  - `ai_done_at` : Date de génération IA

#### `InquiryDocument` (store/models.py:347)
- Fichiers uploadés par le client (max 10 fichiers, 10 Mo chacun)
- Stockage : `inquiries/{inquiry_id}/{filename}`

#### `KitProcessingTask` (store/models.py:358)
- Tâche de traitement (statuts : PENDING, RUNNING, DONE, FAILED, PUBLISHED)
- **Note** : Modèle créé mais pas toujours utilisé (certaines parties utilisent directement `ai_status`)

#### `Order` (store/models.py:100)
- Modèle de commande/paiement existant
- **Statuts** : CREATED, PENDING, PAID, FAILED, CANCELED
- **Intégration CinetPay** : Oui (via `cinetpay_payment_id`, `provider_ref`)
- **❌ PROBLÈME** : Aucune relation avec `ClientInquiry`

---

### 2. **FORMULAIRE DE SOUMISSION**

#### Route : `/kit/inquiry/` (store/urls.py:28)
- **Vue** : `kit_inquiry` (store/views.py:151)
- **Template** : `store/forms/kit_inquiry.html`
- **Limites** :
  - Max 10 fichiers
  - 10 Mo par fichier
  - 15 Mo total
  - Formats autorisés : `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.jpg`, `.jpeg`, `.png`, `.gif`

#### Traitement après soumission :
1. ✅ Création de `ClientInquiry` avec `kind=KIND_KIT`
2. ✅ Création de `InquiryDocument` pour chaque fichier
3. ✅ Création de `KitProcessingTask` (PENDING)
4. ✅ Déclenchement de la tâche Celery `build_kit_word.delay(inquiry.id)`
5. ✅ Envoi email à l'admin (`contact@auditsanspeur.com`)
6. ✅ Redirection vers page de succès

**❌ MANQUE** : Aucune vérification de paiement avant traitement

---

### 3. **GÉNÉRATION IA (TÂCHE CELERY)**

#### Fichier : `store/tasks.py` — Fonction `build_kit_word`
- **Statut** : ✅ Implémenté et fonctionnel
- **Processus** :
  1. Lit les fichiers uploadés (`InquiryDocument`)
  2. Génère le prompt Markdown via template `ai/prompts/kit_complet_consigne.md`
  3. Appel OpenAI API (modèle configuré : `gpt-4o-mini` avec fallbacks)
  4. Convertit la réponse Markdown en DOCX via `store/utils/docx_builder.py`
  5. Sauvegarde dans `PRIVATE_MEDIA_ROOT/kits/ai/kit_{inquiry.id}.docx`
  6. Met à jour `inquiry.ai_doc` et `ai_status = DONE`
  7. **Envoi email automatique au client avec lien signé** (7 jours) — **⚠️ PROBLÈME** : Envoi immédiat sans vérification paiement

#### Configuration OpenAI :
- Variables d'env : `OPENAI_API_KEY`, `OPENAI_ORG`, `OPENAI_PROJECT`, `OPENAI_BASE_URL`
- Modèle : `OPENAI_CHAT_MODEL` (défaut : `gpt-4o-mini`)
- Fallbacks : `OPENAI_CHAT_MODEL_FALLBACKS`

#### Template de prompt :
- Fichier : `auditshield/templates/ai/prompts/kit_complet_consigne.md`
- Inclut toutes les variables du formulaire (via template Django)
- Structure attendue : Introduction, Questionnaires, Irrégularités, Synthèse

---

### 4. **INTERFACE STAFF — TRAITEMENT**

#### Route : `/kit-complet-traitement/` (store/urls.py:32)
- **Vue** : `kit_processing_list` (store/views.py:275)
- **Template** : `store/templates/store/kit_processing_list.html`
- **Accès** : Staff uniquement (`@staff_member_required`)
- **Fonctionnalités** :
  - ✅ Liste des demandes (`ClientInquiry` avec `kind=KIT`)
  - ✅ Téléchargement Word généré par IA
  - ✅ Upload PDF final validé
  - ✅ Bouton "Publier" (envoi lien au client)
  - ✅ Relance traitement IA si erreur
  - ✅ Suppression de demande

#### Routes associées :
- `/kit-complet-traitement/upload-pdf/<id>/` : Upload PDF (staff)
- `/kit-complet-traitement/retry/<id>/` : Relance IA (staff)
- `/kit-complet-traitement/publier/<id>/` : Publication + envoi email (staff)
- `/kit-complet-traitement/delete/<id>/` : Suppression (staff)

---

### 5. **LIENS DE TÉLÉCHARGEMENT**

#### Route : `/kit/download-pdf/<token>/` (store/urls.py:38)
- **Vue** : `kit_download_pdf` (store/views.py:451)
- **Sécurité** :
  - ✅ Token signé avec `TimestampSigner` (validité : 7 jours)
  - ✅ Fichiers stockés dans `PRIVATE_MEDIA_ROOT` (non accessible publiquement)
  - ✅ Vérification existence fichier

#### Route : `/kit/download/<token>/` (store/urls.py:37)
- **Vue** : `kit_download` (store/views.py:425)
- **Usage** : Téléchargement du Word généré par IA (lien envoyé automatiquement après génération)

**❌ PROBLÈME** : Aucune vérification de paiement avant téléchargement

---

### 6. **SYSTÈME DE PAIEMENT EXISTANT**

#### Intégration CinetPay :
- **Fichier** : `store/services/cinetpay.py`
- **Modèle** : `Order` avec statuts PAID/FAILED/PENDING
- **Routes** :
  - `/buy/<slug>/` : Page de checkout
  - `/payments/cinetpay/return/` : Retour après paiement
  - `/payments/cinetpay/notify/` : Webhook CinetPay

#### Fonctionnalités :
- ✅ Création de commande
- ✅ Redirection vers CinetPay
- ✅ Webhook de notification
- ✅ Création de `DownloadToken` après paiement réussi
- ✅ Système de liens sécurisés pour téléchargements

**❌ PROBLÈME** : Aucune intégration avec `ClientInquiry`

---

## ❌ CE QUI MANQUE (PAR RAPPORT À L'OBJECTIF)

### 1. **LIEN ENTRE PAIEMENT ET DEMANDE DE KIT**
- ❌ Aucune relation `ForeignKey` entre `Order` et `ClientInquiry`
- ❌ Pas de vérification de paiement avant traitement IA
- ❌ Pas de vérification de paiement avant envoi du lien au client

### 2. **WORKFLOW CONDITIONNÉ AU PAIEMENT**
- ❌ Le formulaire `/kit/inquiry/` ne demande pas de paiement
- ❌ Le traitement IA démarre immédiatement sans vérification
- ❌ L'email avec lien est envoyé automatiquement après génération IA (sans vérification paiement)
- ❌ La publication `/kit-complet-traitement/publier/` n' vérifie pas le paiement

### 3. **INTÉGRATION PAIEMENT DANS LE WORKFLOW**
**Workflow attendu** :
1. Client soumet formulaire → Création `ClientInquiry` (statut PENDING)
2. **Nouveau** : Redirection vers page de paiement
3. **Nouveau** : Création `Order` lié à `ClientInquiry`
4. **Nouveau** : Vérification paiement avant traitement IA
5. Après paiement → Traitement IA démarre
6. Génération Word → Upload PDF par humain
7. Publication → **Vérification paiement** → Envoi lien sécurisé

**Workflow actuel** :
1. Client soumet formulaire → Création `ClientInquiry` (statut PENDING)
2. ❌ Traitement IA démarre immédiatement (sans paiement)
3. ❌ Email envoyé automatiquement après génération IA
4. Upload PDF par humain
5. Publication → Envoi lien (sans vérification paiement)

---

## 📋 STRUCTURE ACTUELLE DES FICHIERS

### Fichiers clés :
```
auditshield/
├── store/
│   ├── models.py              # ClientInquiry, Order, InquiryDocument
│   ├── views.py               # kit_inquiry, kit_processing_*, kit_download_*
│   ├── tasks.py               # build_kit_word (Celery)
│   ├── urls.py                # Routes /kit/inquiry/, /kit-complet-traitement/
│   ├── services/
│   │   └── cinetpay.py        # Intégration paiement CinetPay
│   └── utils/
│       └── docx_builder.py   # Conversion Markdown → DOCX
├── templates/
│   └── ai/
│       └── prompts/
│           └── kit_complet_consigne.md  # Template prompt IA
└── config/
    └── settings/
        └── base.py            # OPENAI_API_KEY, PRIVATE_MEDIA_ROOT
```

---

## 🔧 CONFIGURATION ACTUELLE

### Variables d'environnement nécessaires :
```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_ORG=org-...              # Optionnel
OPENAI_PROJECT=proj-...         # Optionnel
OPENAI_BASE_URL=...             # Optionnel (pour API alternatives)
OPENAI_CHAT_MODEL=gpt-4o-mini   # Défaut

# CinetPay
CINETPAY_API_KEY=...
CINETPAY_SITE_ID=...
CINETPAY_RETURN_URL=...
CINETPAY_NOTIFY_URL=...

# Django
DJANGO_SECRET_KEY=...
PRIVATE_MEDIA_ROOT=/path/to/private_media  # Fichiers payants
```

### Stockage des fichiers :
- **Fichiers uploadés client** : `MEDIA_ROOT/inquiries/{inquiry_id}/`
- **Word généré par IA** : `PRIVATE_MEDIA_ROOT/kits/ai/kit_{inquiry.id}.docx`
- **PDF validé par humain** : `PRIVATE_MEDIA_ROOT/kits/pdf/kit_{inquiry.id}.pdf`

---

## 🎯 RÉSUMÉ DES MODIFICATIONS NÉCESSAIRES

### 1. **Modèle de données**
- Ajouter `order = ForeignKey(Order, null=True, blank=True)` dans `ClientInquiry`
- Migration nécessaire

### 2. **Formulaire de soumission**
- Modifier `kit_inquiry` pour rediriger vers page de paiement après soumission
- Créer une page de checkout spécifique au kit complet

### 3. **Traitement IA**
- Modifier `build_kit_word` pour vérifier le paiement avant génération
- Ne pas envoyer d'email automatique après génération IA

### 4. **Interface staff**
- Modifier `kit_processing_publish` pour vérifier le paiement avant envoi
- Afficher le statut de paiement dans la liste

### 5. **Téléchargement**
- Modifier `kit_download_pdf` pour vérifier le paiement avant téléchargement
- Ou utiliser le système `DownloadToken` existant

### 6. **Webhook CinetPay**
- Après paiement réussi, vérifier s'il existe un `ClientInquiry` lié
- Déclencher le traitement IA si paiement OK

---

## 📝 NOTES TECHNIQUES

### Celery :
- La tâche `build_kit_word` est configurée comme `@shared_task`
- En mode dev (sans Celery), création de `KitProcessingTask` pour traitement manuel
- Fallback : `CELERY_TASK_ALWAYS_EAGER` pour exécution synchrone

### Sécurité :
- Fichiers dans `PRIVATE_MEDIA_ROOT` (non servis publiquement)
- Tokens signés avec `TimestampSigner` (validité 7 jours)
- Vérification staff pour toutes les opérations de traitement

### Templates :
- Le prompt IA (`kit_complet_consigne.md`) utilise les variables Django du formulaire
- Variables disponibles : `{{ inquiry.contact_name }}`, `{{ inquiry.organization_name }}`, etc.

---

## ✅ PROCHAINES ÉTAPES RECOMMANDÉES

1. **Créer le lien entre Order et ClientInquiry**
2. **Modifier le workflow pour inclure le paiement**
3. **Créer une page de checkout spécifique au kit**
4. **Intégrer la vérification de paiement dans toutes les étapes**
5. **Tester le workflow complet**

---

**Date de création** : 2025-01-XX  
**Dernière mise à jour** : 2025-01-XX

