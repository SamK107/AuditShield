# 📋 RÉSUMÉ EXÉCUTIF — ÉTAT DES LIEUX KIT COMPLET

## 🎯 OBJECTIF FINAL
Workflow : **Formulaire → Paiement → Génération IA → Validation humaine → Envoi lien sécurisé (conditionné au paiement)**

---

## ✅ CE QUI FONCTIONNE

### 1. **Formulaire de soumission** (`/kit/inquiry/`)
- ✅ Collecte données client + fichiers (max 10, 10 Mo chacun)
- ✅ Création `ClientInquiry` + `InquiryDocument`
- ✅ Envoi email admin

### 2. **Génération IA** (`store/tasks.py` → `build_kit_word`)
- ✅ Tâche Celery fonctionnelle
- ✅ Utilise template `kit_complet_consigne.md`
- ✅ Appel OpenAI API (gpt-4o-mini)
- ✅ Conversion Markdown → DOCX
- ✅ Sauvegarde dans `PRIVATE_MEDIA_ROOT/kits/ai/`
- ✅ **⚠️ Envoi email automatique au client** (sans vérification paiement)

### 3. **Interface staff** (`/kit-complet-traitement/`)
- ✅ Liste des demandes
- ✅ Upload PDF validé
- ✅ Publication + envoi lien (token signé 7 jours)
- ✅ Relance IA si erreur

### 4. **Système de paiement** (CinetPay)
- ✅ Modèle `Order` avec statuts PAID/FAILED
- ✅ Intégration CinetPay fonctionnelle
- ✅ Webhook de notification

---

## ❌ CE QUI MANQUE

### 1. **Lien entre paiement et demande**
- ❌ Aucune relation `Order` ↔ `ClientInquiry`
- ❌ Pas de ForeignKey entre les deux modèles

### 2. **Workflow conditionné au paiement**
- ❌ Traitement IA démarre immédiatement (sans paiement)
- ❌ Email envoyé automatiquement après génération IA
- ❌ Pas de vérification paiement avant envoi lien

### 3. **Page de paiement pour kit**
- ❌ Pas de checkout spécifique au kit complet
- ❌ Pas de redirection vers paiement après soumission formulaire

---

## 🔄 WORKFLOW ACTUEL vs ATTENDU

### **ACTUEL** :
```
Formulaire → ClientInquiry créé → IA démarre immédiatement 
→ Email envoyé automatiquement → Upload PDF → Publication → Envoi lien
```

### **ATTENDU** :
```
Formulaire → ClientInquiry créé → Redirection paiement → Order créé
→ Paiement validé → IA démarre → Upload PDF → Publication 
→ Vérification paiement → Envoi lien sécurisé
```

---

## 📦 MODIFICATIONS NÉCESSAIRES

### 1. **Modèle** (`store/models.py`)
```python
# Dans ClientInquiry, ajouter :
order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL)
```

### 2. **Formulaire** (`store/views.py` → `kit_inquiry`)
- Après création `ClientInquiry`, créer `Order` et rediriger vers checkout

### 3. **Traitement IA** (`store/tasks.py` → `build_kit_word`)
- Vérifier `inquiry.order.status == PAID` avant génération
- Ne pas envoyer email automatiquement

### 4. **Publication** (`store/views.py` → `kit_processing_publish`)
- Vérifier paiement avant envoi lien

### 5. **Téléchargement** (`store/views.py` → `kit_download_pdf`)
- Vérifier paiement OU utiliser `DownloadToken` existant

### 6. **Webhook CinetPay**
- Après paiement, chercher `ClientInquiry` lié et déclencher IA

---

## 🗂️ FICHIERS CLÉS

- `store/models.py` : Modèles ClientInquiry, Order
- `store/views.py` : Vues kit_inquiry, kit_processing_*, kit_download_*
- `store/tasks.py` : Tâche Celery build_kit_word
- `store/urls.py` : Routes
- `templates/ai/prompts/kit_complet_consigne.md` : Template prompt IA
- `store/services/cinetpay.py` : Intégration paiement

---

## 🔧 CONFIGURATION

### Variables nécessaires :
- `OPENAI_API_KEY` : Pour génération IA
- `CINETPAY_API_KEY`, `CINETPAY_SITE_ID` : Pour paiement
- `PRIVATE_MEDIA_ROOT` : Stockage fichiers payants

---

## 📝 POUR CHATGPT

**Demande** : Proposer un **Plan d'implémentation (pro & modulaire)** pour intégrer le paiement dans le workflow du Kit Complet, en tenant compte de l'existant décrit ci-dessus.

**Points à considérer** :
- Architecture modulaire (séparation des responsabilités)
- Gestion des erreurs (paiement échoué, IA échouée, etc.)
- Expérience utilisateur (feedback clair à chaque étape)
- Sécurité (vérification paiement, tokens signés)
- Compatibilité avec l'existant (ne pas casser ce qui fonctionne)
- Tests et rollback

