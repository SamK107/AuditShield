# 🧪 Guide de Test - Système IA Kit Complet

**Date :** 7 décembre 2025  
**Objectif :** Tester le système de génération IA des kits complets de préparation à l'audit

---

## ✅ Prérequis

### 1. Clé API OpenAI

Vous devez avoir une clé API OpenAI valide. Si vous n'en avez pas :
1. Allez sur https://platform.openai.com/api-keys
2. Créez une nouvelle clé API
3. Copiez-la (elle commence par `sk-...`)

### 2. Redis (pour Celery)

Vérifiez que Redis est installé et fonctionne :

```bash
# Windows : Installer Redis via WSL ou Docker
# Vérifier si Redis tourne :
redis-cli ping
# Devrait retourner : PONG
```

Si Redis n'est pas installé :
```bash
# Option 1 : Via Docker (recommandé)
docker run -d -p 6379:6379 redis:alpine

# Option 2 : Via WSL (si installé)
sudo apt-get install redis-server
sudo service redis-server start
```

---

## 🔧 Configuration (Étape par Étape)

### Étape 1 : Configurer OpenAI

Ouvrez le fichier `.env` dans le dossier `auditshield/` et ajoutez/modifiez :

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-votre-clé-ici
OPENAI_CHAT_MODEL=gpt-4o-mini

# Si vous avez accès à GPT-4.1-mini :
# OPENAI_CHAT_MODEL=gpt-4.1-mini

# Celery (pour les tâches asynchrones)
CELERY_BROKER_URL=redis://localhost:6379/0
```

**Vérification :**
```bash
cd auditshield
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('OPENAI_API_KEY')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'MANQUANTE')"
```

### Étape 2 : Vérifier les dépendances

```bash
# Activer l'environnement virtuel
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1

cd auditshield

# Vérifier les packages installés
pip list | Select-String -Pattern "openai|celery|redis|docx|pdfplumber"
```

**Packages nécessaires :**
- ✅ `openai` (>= 1.0.0)
- ✅ `python-docx` (>= 0.8.11)
- ✅ `pdfplumber` ou `pypdf` (>= 0.10.0)
- ✅ `celery` (>= 5.3.0)
- ✅ `redis` (>= 5.0.0)

Si manquants :
```bash
pip install openai python-docx pdfplumber celery redis
```

### Étape 3 : Vérifier le fichier de consignes

```bash
# Vérifier que le fichier existe
ls assets/Modele_Consignes_Kit_Complet.md
```

Si le fichier existe, vous verrez :
```
assets/Modele_Consignes_Kit_Complet.md
```

---

## 🚀 Lancement du Test

### Terminal 1 : Démarrer le serveur Django

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield

# Démarrer le serveur
python manage.py runserver
```

**Sortie attendue :**
```
System check identified no issues (0 silenced).
December 07, 2025 - 13:00:00
Django version 4.2.26, using settings 'config.settings.development'
Starting development server at http://127.0.0.1:8000/
```

### Terminal 2 : Démarrer Celery Worker

**Ouvrez un NOUVEAU terminal** :

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield

# Démarrer Celery (mode verbeux pour voir les logs)
celery -A config worker -l info
```

**Sortie attendue :**
```
 -------------- celery@VOTRE-PC v5.3.x
---- **** ----- 
--- * ***  * -- Windows-10-... 2025-12-07 13:00:00
-- * - **** --- 
- ** ---------- [config]
- ** ---------- .> app:         config:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     disabled://
- *** --- * --- .> concurrency: 4 (prefork)
-- ******* ---- .> task events: OFF
--- ***** ----- 
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . store.tasks.run_kit_ai_pipeline
  . store.tasks.build_kit_word
  ...

[2025-12-07 13:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-12-07 13:00:00,000: INFO/MainProcess] mingle: searching for neighbors
[2025-12-07 13:00:00,000: INFO/MainProcess] mingle: all alone
[2025-12-07 13:00:00,000: INFO/MainProcess] celery@VOTRE-PC ready.
```

✅ **Si vous voyez "celery@... ready.", Celery fonctionne !**

❌ **Si erreur "Cannot connect to redis" :**
- Vérifiez que Redis tourne : `redis-cli ping`
- Vérifiez `CELERY_BROKER_URL` dans `.env`

---

## 🧪 Test Complet du Système

### Préparation : Créer une demande de test

#### Option 1 : Via l'admin Django (Recommandé)

1. **Accédez à l'admin Django** :
   ```
   http://localhost:8000/admin/
   ```

2. **Connectez-vous** avec un compte staff/superuser

3. **Créez une ClientInquiry de test** :
   - Allez dans **Store → Client inquiries**
   - Cliquez sur **Add Client Inquiry**
   - Remplissez :
     - **Kind** : Kit personnalisé
     - **Contact name** : Test User
     - **Email** : test@example.com
     - **Organization name** : Mairie de Test
     - **Context text** : "Structure publique de 50 agents..."
     - **Payment status** : PAID
     - **Processing state** : PAID
   - Cliquez sur **Save**

4. **Uploadez des documents de test** :
   - Dans la même page, section **Documents**
   - Cliquez sur **Add another Inquiry Document**
   - Uploadez un fichier PDF ou TXT de test
   - **Fichier de test suggéré** : Créez un fichier `test_document.txt` avec :
     ```
     Règlement Intérieur de la Mairie de Test
     
     Article 1 : Organisation
     La mairie est organisée en 3 services : finances, urbanisme, état civil.
     
     Article 2 : Contrôles
     Des audits internes sont réalisés annuellement.
     
     Article 3 : Documents obligatoires
     - Registre des délibérations
     - Livre de comptes
     - Inventaire du patrimoine
     ```

5. **Notez l'ID de l'inquiry** (par ex. : #42)

#### Option 2 : Via la console Django

```bash
python manage.py shell
```

```python
from store.models import ClientInquiry, InquiryDocument
from django.core.files.base import ContentFile

# Créer une inquiry de test
inquiry = ClientInquiry.objects.create(
    kind="KIT",
    contact_name="Test User",
    email="test@example.com",
    organization_name="Mairie de Test",
    context_text="Structure publique de 50 agents gérant les services municipaux.",
    payment_status="PAID",
    processing_state="PAID"
)

# Créer un document de test
test_content = """Règlement Intérieur de la Mairie de Test

Article 1 : Organisation
La mairie est organisée en 3 services : finances, urbanisme, état civil.

Article 2 : Contrôles
Des audits internes sont réalisés annuellement.

Article 3 : Documents obligatoires
- Registre des délibérations
- Livre de comptes
- Inventaire du patrimoine
"""

doc = InquiryDocument.objects.create(
    inquiry=inquiry,
    original_name="test_reglement.txt"
)
doc.file.save("test_reglement.txt", ContentFile(test_content.encode()))

print(f"✅ Inquiry de test créée : ID = {inquiry.pk}")
print(f"✅ URL de test : http://localhost:8000/kit-complet-traitement/")
```

---

### 🎬 Exécution du Test

#### Étape 1 : Accéder à la page de traitement

Ouvrez votre navigateur :
```
http://localhost:8000/kit-complet-traitement/
```

**Ce que vous devriez voir :**
- Un tableau avec votre inquiry de test
- Colonne "Statut" : Badge bleu "PAID"
- Colonne "Traiter" : Bouton bleu "Traiter avec l'IA"

#### Étape 2 : Lancer le traitement IA

1. **Cliquez sur "Traiter avec l'IA"**

**Ce qui se passe immédiatement :**
- ✅ Message vert : "Traitement IA lancé. Le brouillon sera disponible dès qu'il sera prêt."
- ✅ Colonne "Statut" : Badge orange "IA_RUNNING"
- ✅ Colonne "Traiter" : Spinner animé "IA en cours…"

**Dans le terminal Celery, vous devriez voir :**
```
[INFO] Task store.tasks.run_kit_ai_pipeline[<task-id>] received
[INFO] [run_kit_ai_pipeline] Début du traitement pour task <task-id>, inquiry 42
[INFO] [Ollama] Appel API sur http://... (ou OpenAI)
...
```

#### Étape 3 : Attendre la génération (30-60 secondes)

**Progression dans le terminal Celery :**
```
[INFO] Extraction des documents...
[INFO] Construction du prompt...
[INFO] Appel OpenAI GPT-4o-mini...
[INFO] Génération réussie (X caractères)
[INFO] Conversion Markdown → DOCX...
[INFO] Sauvegarde dans GeneratedDraft...
[INFO] Task completed successfully
```

#### Étape 4 : Rafraîchir la page

Après 30-60 secondes, **rafraîchissez la page** (F5)

**Ce que vous devriez voir :**
- ✅ Colonne "Statut" : Badge violet "DRAFT_DONE"
- ✅ Colonne "Traiter" : "—" (grisé)
- ✅ Colonne "Télécharger (IA)" : **Bouton vert "Télécharger le brouillon"**

#### Étape 5 : Télécharger le brouillon

1. **Cliquez sur "Télécharger le brouillon"**
2. Un fichier Word `kit_inquiry_42.docx` est téléchargé
3. **Ouvrez le fichier Word**

**Contenu attendu du DOCX :**
```
# Kit complet de préparation à l'audit

## Introduction générale
...présentation adaptée à la Mairie de Test...

## Questionnaires de préparation

### Questions relatives au Règlement Intérieur
1. Le registre des délibérations est-il à jour ?
2. Les 3 services (finances, urbanisme, état civil) sont-ils clairement organisés ?
...

## Tableaux d'irrégularités

| Irrégularité | Référence | Acteurs | Dispositions |
|--------------|-----------|---------|--------------|
| Absence de livre de comptes | Article 3 | Service finances | Mettre en place... |
...

## Synthèse et recommandations
...

## Plan d'action
...
```

✅ **Si vous voyez un document structuré avec du contenu pertinent → LE SYSTÈME FONCTIONNE !**

#### Étape 6 : Tester l'upload de la version finale

1. **Modifiez le Word téléchargé** (ajoutez une section, corrigez, etc.)
2. **Sauvegardez-le** (par ex. : `kit_inquiry_42_final.docx`)
3. **Dans la colonne "Upload Final"** :
   - Cliquez sur "Parcourir"
   - Sélectionnez votre fichier modifié
   - Cliquez sur "📤 Upload Final"

**Résultat attendu :**
- ✅ Message vert : "Version finale uploadée avec succès"
- ✅ Colonne "Statut" : Badge rose "FINAL_UPLOADED"
- ✅ Colonne "Actions" : Nouveau lien "✅ Version finale"
- ✅ Colonne "Publier" : **Bouton vert "Publier"** actif

#### Étape 7 : Tester la publication (Optionnel)

⚠️ **Attention : Ceci enverra un email au client !**

1. **Cliquez sur "Publier"**

**Résultat attendu :**
- ✅ Email envoyé à `test@example.com`
- ✅ Colonne "Statut" : Badge vert "PUBLISHED"
- ✅ Ligne du tableau : Fond vert clair

---

## 📊 Vérification des Logs

### Logs Django

```bash
# Dans le terminal 1 (Django), vous devriez voir :
POST /kit-complet-traitement/42/process/ 302
GET /kit-complet-traitement/ 200
```

### Logs Celery

```bash
# Dans le terminal 2 (Celery), vous devriez voir :
[INFO] Task store.tasks.run_kit_ai_pipeline[...] received
[INFO] [run_kit_ai_pipeline] Début du traitement pour task ..., inquiry 42
[INFO] [Ollama] Appel API sur ...
[INFO] [Ollama] Génération réussie (X caractères)
[INFO] [run_kit_ai_pipeline] Traitement terminé avec succès pour task ..., inquiry 42
[INFO] Task store.tasks.run_kit_ai_pipeline[...] succeeded in 45.2s
```

### Base de données (Vérification manuelle)

```bash
python manage.py shell
```

```python
from store.models import ClientInquiry, GeneratedDraft, KitProcessingTask

# Récupérer l'inquiry de test
inquiry = ClientInquiry.objects.get(pk=42)  # Remplacez 42 par votre ID

# Vérifier le statut
print(f"Processing state: {inquiry.processing_state}")  # DRAFT_DONE
print(f"AI status: {inquiry.ai_status}")  # done

# Vérifier le brouillon généré
draft = inquiry.generated_draft
print(f"Draft existe: {draft is not None}")
print(f"Draft DOCX: {draft.docx.url}")
print(f"Modèle utilisé: {draft.model_name}")
print(f"Tokens utilisés: {draft.token_usage}")

# Vérifier les tâches
tasks = inquiry.tasks.all()
print(f"Nombre de tâches: {tasks.count()}")
for task in tasks:
    print(f"  - Task {task.id}: {task.status}")
```

---

## ❌ Troubleshooting

### Problème 1 : "OPENAI_API_KEY n'est pas configurée"

**Solution :**
```bash
# Vérifier que le .env est bien lu
cd auditshield
python -c "from django.conf import settings; print(settings.OPENAI_API_KEY)"
```

Si vide :
1. Ouvrez `.env`
2. Ajoutez `OPENAI_API_KEY=sk-...`
3. Redémarrez Django et Celery

### Problème 2 : "Cannot connect to redis"

**Solution :**
```bash
# Vérifier Redis
redis-cli ping
# Devrait retourner : PONG
```

Si Redis ne répond pas :
```bash
# Option 1 : Docker
docker run -d -p 6379:6379 redis:alpine

# Option 2 : WSL
sudo service redis-server start
```

### Problème 3 : Task reste en "RUNNING" indéfiniment

**Causes possibles :**
1. Celery n'est pas démarré → Vérifier Terminal 2
2. Erreur dans le code → Consulter les logs Celery
3. OpenAI timeout → Augmenter le timeout dans settings

**Debug :**
```bash
# Dans le terminal Celery, chercher :
[ERROR] ...
Traceback ...
```

### Problème 4 : "Fichier de consignes introuvable"

**Solution :**
```bash
# Vérifier que le fichier existe
ls assets/Modele_Consignes_Kit_Complet.md
```

Si manquant, le système utilise un fallback basique (le test fonctionnera quand même).

### Problème 5 : Erreur OpenAI "Quota exceeded"

**Solution :**
1. Vérifiez votre compte OpenAI : https://platform.openai.com/account/usage
2. Ajoutez des crédits si nécessaire
3. Ou utilisez un modèle moins cher : `OPENAI_CHAT_MODEL=gpt-3.5-turbo`

### Problème 6 : Le DOCX est vide ou mal formaté

**Vérifier :**
```python
# Console Django
from store.models import ClientInquiry
inquiry = ClientInquiry.objects.get(pk=42)
draft = inquiry.generated_draft

# Voir les logs
print(draft.log)

# Voir le contenu brut
with draft.docx.open('rb') as f:
    print(f"Taille du fichier: {len(f.read())} bytes")
```

---

## ✅ Checklist de Test Complet

### Configuration
- [ ] `.env` configuré avec `OPENAI_API_KEY`
- [ ] Redis fonctionne (`redis-cli ping`)
- [ ] Packages installés (`pip list`)
- [ ] Fichier de consignes existe

### Démarrage
- [ ] Django tourne (Terminal 1)
- [ ] Celery tourne (Terminal 2)
- [ ] Aucune erreur dans les logs

### Test Fonctionnel
- [ ] Inquiry de test créée (avec document)
- [ ] Page `/kit-complet-traitement/` accessible
- [ ] Clic "Traiter avec l'IA" fonctionne
- [ ] Statut passe à "IA_RUNNING"
- [ ] Task Celery se lance (logs visibles)
- [ ] Statut passe à "DRAFT_DONE" (après 30-60s)
- [ ] Bouton "Télécharger le brouillon" visible
- [ ] DOCX téléchargé et contient du contenu pertinent
- [ ] Upload de la version finale fonctionne
- [ ] Bouton "Publier" devient actif
- [ ] Publication fonctionne (email envoyé)

---

## 📈 Métriques de Performance

### Timing Normal
- **Extraction documents** : 2-10 secondes
- **Appel OpenAI** : 15-45 secondes
- **Génération DOCX** : 1-3 secondes
- **Total** : **20-60 secondes**

### Coût OpenAI (GPT-4o-mini)
- **Input** : ~3000-8000 tokens
- **Output** : ~2000-5000 tokens
- **Coût** : **$0.01-0.03 par kit**

### Qualité du Résultat
Le DOCX généré devrait contenir :
- ✅ Introduction adaptée au contexte
- ✅ 10-20 questions pertinentes
- ✅ 5-15 irrégularités identifiées
- ✅ Recommandations pratiques
- ✅ Plan d'action priorisé

---

## 🎉 Félicitations !

Si tous les tests sont ✅, votre système IA est **100% opérationnel** ! 🚀

**Prochaines étapes suggérées :**
1. Tester avec des documents réels
2. Ajuster le fichier de consignes si nécessaire
3. Former l'équipe staff à l'utilisation
4. Monitorer les coûts OpenAI
5. Mettre en production !

---

**Besoin d'aide ?**
- Consultez `IMPLEMENTATION_IA_GPT_KIT_COMPLET.md`
- Vérifiez les logs Django : `logs/app.log`
- Vérifiez les logs Celery : Terminal 2

**Support :**
- Documentation OpenAI : https://platform.openai.com/docs
- Documentation Celery : https://docs.celeryq.dev

