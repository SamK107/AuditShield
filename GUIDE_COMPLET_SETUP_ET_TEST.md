# 🎯 Guide Complet : Setup & Test du Système IA - AuditShield

**Date :** 7 décembre 2025  
**Objectif :** Configurer et tester le système de génération IA pour les kits complets

---

## 📚 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Configuration OpenAI](#1-configuration-openai)
3. [Installation Redis](#2-installation-redis)
4. [Démarrage du Système](#3-démarrage-du-système)
5. [Test Fonctionnel](#4-test-fonctionnel)
6. [Dépannage](#5-dépannage)
7. [Documentation](#6-documentation)

---

## Vue d'Ensemble

### ✅ Ce Qui Est Déjà Prêt

Votre projet AuditShield a **TOUT le code nécessaire** déjà implémenté :

```
✅ Modèles Django (ClientInquiry, GeneratedDraft, etc.)
✅ Services IA (core/ai/kit_builder.py, kit_utils.py)
✅ Task Celery (store/tasks.py)
✅ Vues Django (store/views_admin_kit.py)
✅ Template UI (kit_complete_processing.html)
✅ URLs configurées
✅ Extraction documents (PDF, DOCX, TXT)
✅ Génération DOCX professionnelle
✅ Gestion d'erreurs robuste
```

### ⚠️ Ce Qu'il Manque (Configuration uniquement)

```
❌ Clé API OpenAI (à ajouter dans .env)
❌ Redis (à installer et démarrer)
```

**Une fois ces 2 éléments configurés → Le système fonctionne ! 🚀**

---

## 1. Configuration OpenAI

### Étape A : Obtenir la Clé

**Si vous avez déjà un compte OpenAI :**

1. 🌐 Allez sur : https://platform.openai.com/api-keys
2. 🔑 Cliquez sur "Create new secret key"
3. 📝 Nom : "AuditShield-Production"
4. 📋 Copiez la clé (commence par `sk-...`)

**Si vous n'avez PAS de compte :**

1. 🌐 Allez sur : https://platform.openai.com/signup
2. 📧 Créez un compte
3. 💳 Ajoutez une méthode de paiement (~$5 minimum)
4. 🔑 Créez une clé (voir ci-dessus)

### Étape B : Ajouter la Clé

```bash
# Ouvrir le fichier .env
notepad C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield\.env
```

**Ajoutez/modifiez ces lignes :**

```bash
# === OPENAI CONFIGURATION ===
OPENAI_API_KEY=sk-votre-clé-complète-ici-sans-espace
OPENAI_CHAT_MODEL=gpt-4o-mini

# Si vous avez accès à GPT-4.1-mini (plus récent) :
# OPENAI_CHAT_MODEL=gpt-4.1-mini
```

**Sauvegardez** (Ctrl+S) et fermez.

### Étape C : Vérification

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py shell
```

```python
import os
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✅ Clé configurée : {api_key[:10]}...{api_key[-4:]}")
else:
    print("❌ Clé MANQUANTE")
exit()
```

**📖 Guide détaillé :** `SETUP_OPENAI_KEY.md`

---

## 2. Installation Redis

### Option 1 : Docker (⭐ Recommandé - Le Plus Simple)

#### Installer Docker Desktop

1. **Téléchargez** : https://www.docker.com/products/docker-desktop
2. **Installez** Docker Desktop
3. **Lancez** l'application Docker Desktop
4. **Attendez** que l'icône Docker devienne verte (barre des tâches)

#### Lancer Redis

```bash
# Une seule commande !
docker run -d -p 6379:6379 --name auditshield-redis redis:alpine
```

**Explication :**
- Redis s'installe automatiquement (30 MB)
- Démarre en arrière-plan
- Accessible sur `localhost:6379`

#### Vérification

```bash
# Voir si Redis tourne
docker ps

# Devrait afficher :
# CONTAINER ID   IMAGE          STATUS        PORTS                    NAMES
# abc123...      redis:alpine   Up 1 minute   0.0.0.0:6379->6379/tcp   auditshield-redis
```

#### Test de Connexion

```bash
# Test via Docker
docker exec -it auditshield-redis redis-cli ping
# Devrait retourner : PONG
```

✅ **Si vous voyez "PONG" → Redis fonctionne !**

#### Commandes Utiles

```bash
# Arrêter Redis
docker stop auditshield-redis

# Redémarrer Redis
docker start auditshield-redis

# Voir les logs
docker logs auditshield-redis

# Redis au démarrage Windows (optionnel)
docker update --restart=always auditshield-redis
```

---

### Option 2 : WSL2 (Si vous n'avez pas Docker)

```bash
# 1. Installer WSL2
wsl --install
# Redémarrer Windows

# 2. Lancer WSL
wsl

# 3. Installer Redis
sudo apt update
sudo apt install redis-server -y

# 4. Démarrer Redis
sudo service redis-server start

# 5. Test
redis-cli ping
# Devrait retourner : PONG
```

---

### Option 3 : Memurai (Redis natif Windows)

1. **Téléchargez** : https://www.memurai.com/get-memurai
2. **Installez** l'exe
3. **Redis démarre automatiquement** comme service Windows
4. **Test** : `redis-cli ping` dans CMD

---

### Configuration AuditShield

**Vérifiez le `.env` :**

```bash
notepad C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield\.env
```

**Doit contenir :**
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
```

**📖 Guide détaillé :** `SETUP_REDIS.md`

---

## 3. Démarrage du Système

### Terminal 1 : Django

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py runserver
```

**Vous devriez voir :**
```
System check identified no issues (0 silenced).
December 07, 2025 - 14:00:00
Django version 4.2.26
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

✅ **Django tourne !**

---

### Terminal 2 : Celery

**Ouvrez un NOUVEAU terminal PowerShell :**

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
celery -A config worker -l info
```

**Vous devriez voir :**
```
 -------------- celery@VOTRE-PC v5.3.x
...
[tasks]
  . store.tasks.run_kit_ai_pipeline
  . store.tasks.build_kit_word
  ...

[INFO] Connected to redis://localhost:6379/0
[INFO] celery@VOTRE-PC ready.
```

✅ **Si vous voyez "ready." → Celery fonctionne !**

---

## 4. Test Fonctionnel

### Créer une Demande de Test

**Terminal 3 (nouveau PowerShell) :**

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py shell
```

**Copiez-collez ce code Python :**

```python
from store.models import ClientInquiry, InquiryDocument
from django.core.files.base import ContentFile

# Créer une inquiry de test
inquiry = ClientInquiry.objects.create(
    kind="KIT",
    contact_name="Test Utilisateur",
    email="test@example.com",
    organization_name="Mairie de Test",
    context_text="Administration municipale de 50 agents",
    payment_status="PAID",
    processing_state="PAID"
)

# Ajouter un document test
doc_text = """RÈGLEMENT INTÉRIEUR

Article 1 : Organisation
- Service finances
- Service urbanisme
- Service état civil

Article 2 : Contrôles
Audits annuels obligatoires.

Article 3 : Documents
- Registre délibérations
- Livre de comptes
- Inventaire patrimoine
"""

doc = InquiryDocument.objects.create(inquiry=inquiry, original_name="reglement.txt")
doc.file.save("reglement.txt", ContentFile(doc_text.encode()))

print(f"\n✅ Demande créée : ID = {inquiry.pk}\n")
print("🌐 URL : http://localhost:8000/kit-complet-traitement/\n")

exit()
```

---

### Lancer le Test

1. **Ouvrez votre navigateur** : http://localhost:8000/kit-complet-traitement/

2. **Connectez-vous** (compte staff/admin)

3. **Cliquez** sur "Traiter avec l'IA"

4. **Observez** :
   - Message : "Traitement IA lancé..."
   - Statut : "IA_RUNNING" (orange)
   - Terminal 2 : Logs Celery

5. **Attendez** 30-60 secondes

6. **Rafraîchissez** (F5)

7. **Cliquez** sur "Télécharger le brouillon"

8. **Ouvrez** le fichier Word téléchargé

---

### Résultat Attendu

Le document Word devrait contenir :

```
# Kit complet de préparation à l'audit

## Introduction générale
[Texte adapté à la Mairie de Test...]

## Questionnaires de préparation
1. Les 3 services sont-ils clairement définis ?
2. Les audits annuels sont-ils réalisés ?
...

## Tableaux d'irrégularités
| Irrégularité | Référence | Dispositions |
|--------------|-----------|--------------|
| [Irrégularités détectées...]

## Synthèse et recommandations
[Recommandations pratiques...]

## Plan d'action
[Étapes concrètes...]
```

✅ **Si le document est bien structuré → SUCCÈS TOTAL ! 🎉**

---

## 5. Dépannage

### ❌ Erreur : "OPENAI_API_KEY n'est pas configurée"

**Solution :**
```bash
# 1. Vérifier le .env
notepad C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield\.env

# 2. Vérifier qu'il contient :
OPENAI_API_KEY=sk-...

# 3. Redémarrer Django (Ctrl+C dans Terminal 1, puis relancer)
```

---

### ❌ Erreur : "Cannot connect to redis"

**Solution :**
```bash
# Vérifier Redis
docker ps | Select-String redis

# Si vide, démarrer :
docker start auditshield-redis

# Si n'existe pas, créer :
docker run -d -p 6379:6379 --name auditshield-redis redis:alpine
```

---

### ❌ Task reste en "IA_RUNNING" indéfiniment

**Causes :**
1. Celery pas démarré → Vérifier Terminal 2
2. Erreur OpenAI → Consulter logs Celery
3. Redis déconnecté → Test : `docker exec auditshield-redis redis-cli ping`

**Debug :**
```python
# Shell Django
from store.models import KitProcessingTask
tasks = KitProcessingTask.objects.filter(status='RUNNING').order_by('-created_at')
if tasks.exists():
    t = tasks.first()
    print(f"Task {t.id} - Started: {t.started_at}")
    if t.error:
        print(f"Error: {t.error}")
```

---

### ❌ Erreur : "Quota exceeded"

**Solution :**
1. Vérifiez : https://platform.openai.com/account/usage
2. Ajoutez des crédits
3. Ou temporairement : `OPENAI_CHAT_MODEL=gpt-3.5-turbo` (moins cher)

---

### ❌ Le brouillon téléchargé est vide

**Debug :**
```python
# Shell Django
from store.models import ClientInquiry
inquiry = ClientInquiry.objects.get(pk=XX)  # Votre ID

if hasattr(inquiry, 'generated_draft'):
    draft = inquiry.generated_draft
    print(f"Model: {draft.model_name}")
    print(f"Tokens: {draft.token_usage}")
    print(f"\nLog:\n{draft.log}")
else:
    print("❌ Pas de draft généré")
```

---

## 6. Documentation

### 📖 Guides Créés

| Fichier | Objectif | Quand ? |
|---------|----------|---------|
| **START_HERE.md** | Démarrage ultra-rapide | 🔥 Commencez ici ! |
| **SETUP_OPENAI_KEY.md** | Config détaillée OpenAI | Si problème clé |
| **SETUP_REDIS.md** | Installation Redis détaillée | Si problème Redis |
| **QUICK_TEST_GUIDE.md** | Test en 5 minutes | Après config |
| **TEST_KIT_IA_GUIDE.md** | Test complet | Pour tout comprendre |
| **IMPLEMENTATION_IA_GPT_KIT_COMPLET.md** | Architecture | Pour dev/maintenance |
| **GUIDE_COMPLET_SETUP_ET_TEST.md** | Ce fichier | Vue d'ensemble |

---

## 🎯 Parcours Recommandé

### Pour Débutant

1. **START_HERE.md** (5 min)
2. **SETUP_OPENAI_KEY.md** (3 min)
3. **SETUP_REDIS.md** (5 min)
4. **QUICK_TEST_GUIDE.md** (10 min)
5. ✅ **Test réussi !**

### Pour Expert

1. **IMPLEMENTATION_IA_GPT_KIT_COMPLET.md** (architecture)
2. **TEST_KIT_IA_GUIDE.md** (tests exhaustifs)
3. Adaptations personnalisées

---

## 🚀 Commandes de Référence

### Démarrage Complet (3 Terminaux)

```bash
# Terminal 1 - Redis (Docker)
docker start auditshield-redis

# Terminal 2 - Django
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py runserver

# Terminal 3 - Celery
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
celery -A config worker -l info
```

### Vérifications Rapides

```bash
# Redis fonctionne ?
docker exec auditshield-redis redis-cli ping
# Résultat : PONG

# OpenAI configurée ?
python manage.py shell -c "import os; print('OK' if os.getenv('OPENAI_API_KEY') else 'KO')"

# Django OK ?
python manage.py check
# Résultat : System check identified no issues
```

---

## 📊 Architecture du Système

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                           │
│              /kit-complet-traitement/                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ POST /kit-complet/<pk>/process/
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│               DJANGO VIEW (Synchrone)                           │
│         kit_complete_process(request, pk)                       │
│  1. Vérifie paiement                                           │
│  2. Crée KitProcessingTask                                     │
│  3. Met inquiry.processing_state = "IA_RUNNING"                │
│  4. Lance run_kit_ai_pipeline.delay()                          │
│  5. Redirige vers la liste                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Celery Task (Asynchrone)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│           CELERY WORKER (Tâche Asynchrone)                      │
│         run_kit_ai_pipeline(task_id)                            │
│                                                                 │
│  1. Charge consignes (assets/Modele_Consignes...md)           │
│  2. Extrait texte documents (kit_utils.extract_texts...)       │
│     → Supporte PDF, DOCX, TXT                                  │
│  3. Appelle OpenAI GPT (kit_builder.build_kit_markdown)        │
│     → Envoie prompt structuré                                  │
│     → Reçoit Markdown du kit complet                           │
│  4. Convertit Markdown → DOCX (kit_utils.markdown_to_docx)     │
│  5. Sauvegarde dans GeneratedDraft                             │
│  6. Met processing_state = "DRAFT_DONE"                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   DATABASE (PostgreSQL)                         │
│  - ClientInquiry (processing_state = "DRAFT_DONE")             │
│  - GeneratedDraft (docx = fichier Word généré)                 │
│  - KitProcessingTask (status = "DONE")                         │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Rafraîchissement page (F5)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Browser)                           │
│  → Badge violet "DRAFT_DONE"                                   │
│  → Bouton vert "Télécharger le brouillon"                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist Complète

### Configuration (À faire une seule fois)

- [ ] Docker Desktop installé (ou WSL/Memurai)
- [ ] Redis installé et démarré
- [ ] Test : `docker exec auditshield-redis redis-cli ping` → PONG
- [ ] Compte OpenAI créé
- [ ] Clé API OpenAI obtenue
- [ ] Clé ajoutée dans `.env`
- [ ] Test : Clé visible dans Django shell
- [ ] Budget OpenAI configuré (recommandé)

### Démarrage (À chaque session de travail)

- [ ] Redis démarré : `docker start auditshield-redis`
- [ ] Django démarré (Terminal 1)
- [ ] Celery démarré (Terminal 2)
- [ ] Message "celery ready" affiché
- [ ] Page accessible : http://localhost:8000/kit-complet-traitement/

### Test Fonctionnel (Première fois)

- [ ] Demande de test créée (via shell)
- [ ] Demande visible sur la page
- [ ] Clic "Traiter avec l'IA"
- [ ] Statut → "IA_RUNNING"
- [ ] Logs visibles dans Terminal 2
- [ ] Statut → "DRAFT_DONE" (après 30-60s)
- [ ] Brouillon téléchargé
- [ ] Document Word bien formaté avec contenu pertinent

---

## 💰 Coûts et Performance

### Coûts (GPT-4o-mini)

- **Par kit** : $0.01-0.03 (1-3 centimes)
- **50 kits/mois** : ~$1.50
- **200 kits/mois** : ~$6.00

### Performance

- **Temps total** : 30-60 secondes
  - Extraction : 5-15s
  - OpenAI : 15-45s
  - DOCX : 2-5s

### Qualité

- ✅ Introduction adaptée au contexte
- ✅ 10-20 questions pratiques
- ✅ 5-15 irrégularités identifiées
- ✅ Recommandations concrètes
- ✅ Plan d'action priorisé

---

## 🎉 Félicitations !

Si vous avez suivi ce guide, vous avez maintenant :

✅ **OpenAI configuré** (clé API + modèle)  
✅ **Redis installé** (Docker/WSL/Memurai)  
✅ **Système testé** (brouillon généré)  
✅ **Documentation complète** (6 guides)  

**Votre système IA est opérationnel ! 🚀**

---

## 📞 Besoin d'Aide ?

1. **Consultez** `TEST_KIT_IA_GUIDE.md` → Troubleshooting exhaustif
2. **Vérifiez** les logs :
   - Django : `logs/app.log`
   - Celery : Terminal 2
3. **Testez** les commandes de vérification ci-dessus

---

## 🎯 Prochaines Étapes

1. **✅ Testez avec vos documents réels**
2. **📝 Ajustez les consignes** (`assets/Modele_Consignes_Kit_Complet.md`)
3. **📊 Monitorez les coûts** (OpenAI usage)
4. **👥 Formez votre équipe** (avec `QUICK_TEST_GUIDE.md`)
5. **🚀 Mettez en production** !

---

**Bon test ! 🧪**

*Guide créé le 7 décembre 2025*

