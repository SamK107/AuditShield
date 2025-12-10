# 🚀 Guide de Test Rapide - Système IA Kit Complet

## ⚡ Test en 5 Minutes

### ✅ Prérequis Rapides

1. **Clé OpenAI** : Ajoutez dans `.env` :
   ```
   OPENAI_API_KEY=sk-votre-clé
   ```

2. **Redis** (pour Celery) :
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

---

## 🎬 Lancer le Test

### Terminal 1 : Django
```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py runserver
```

### Terminal 2 : Celery
```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
celery -A config worker -l info
```

---

## 🧪 Test Fonctionnel

### 1. Créer une Demande de Test (Console Django)

Ouvrez un nouveau terminal :
```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py shell
```

Dans le shell Python :
```python
from store.models import ClientInquiry, InquiryDocument
from django.core.files.base import ContentFile

# Créer une inquiry de test
inquiry = ClientInquiry.objects.create(
    kind="KIT",
    contact_name="Test User",
    email="test@example.com",
    organization_name="Mairie de Test",
    context_text="Administration publique de 50 agents",
    payment_status="PAID",
    processing_state="PAID"
)

# Ajouter un document de test
test_doc = """RÈGLEMENT INTÉRIEUR - MAIRIE DE TEST

Article 1 : Organisation
La mairie est organisée en 3 services principaux :
- Service des finances
- Service de l'urbanisme  
- Service de l'état civil

Article 2 : Contrôles internes
Des audits internes sont réalisés annuellement par le contrôleur interne.

Article 3 : Documents obligatoires
La mairie doit tenir à jour :
- Le registre des délibérations du conseil municipal
- Le livre des comptes et budgets
- L'inventaire du patrimoine communal
- Les registres d'état civil

Article 4 : Procédures financières
Tout engagement de dépense supérieur à 5000 FCFA nécessite une autorisation du maire.
"""

doc = InquiryDocument.objects.create(
    inquiry=inquiry,
    original_name="reglement_interieur.txt"
)
doc.file.save("reglement.txt", ContentFile(test_doc.encode()))

print(f"✅ Inquiry créée : ID = {inquiry.pk}")
print(f"✅ Document ajouté")
print(f"🌐 Testez sur : http://localhost:8000/kit-complet-traitement/")

# Quitter le shell
exit()
```

### 2. Accéder à l'Interface

Ouvrez votre navigateur :
```
http://localhost:8000/kit-complet-traitement/
```

**Vous devriez voir :**
- Votre demande de test dans le tableau
- Statut : Badge bleu "PAID"
- Bouton : "Traiter avec l'IA" (bleu)

### 3. Lancer le Traitement IA

1. **Cliquez sur "Traiter avec l'IA"**
2. **Message vert** : "Traitement IA lancé..."
3. **Statut change** : "IA_RUNNING" (badge orange)
4. **Colonne "Traiter"** : Spinner "IA en cours…"

### 4. Observer les Logs Celery

Dans le Terminal 2 (Celery), vous devriez voir :
```
[INFO] Task store.tasks.run_kit_ai_pipeline[...] received
[INFO] Extraction des documents...
[INFO] Appel OpenAI GPT-4o-mini...
[INFO] Génération réussie...
[INFO] Conversion Markdown → DOCX...
[INFO] Task succeeded in 45.2s
```

### 5. Attendre 30-60 secondes

Rafraîchissez la page (F5)

**Vous devriez voir :**
- ✅ Statut : "DRAFT_DONE" (badge violet)
- ✅ Bouton vert : "Télécharger le brouillon"

### 6. Télécharger le Brouillon

1. Cliquez sur "Télécharger le brouillon"
2. Un fichier `kit_inquiry_XX.docx` est téléchargé
3. Ouvrez-le avec Word

**Le document devrait contenir :**
- Introduction adaptée à la Mairie de Test
- Questionnaires de préparation (10-20 questions)
- Tableaux d'irrégularités
- Recommandations pratiques
- Plan d'action

---

## ✅ Succès !

Si vous voyez un document Word bien structuré avec du contenu pertinent :

🎉 **LE SYSTÈME FONCTIONNE À 100% !**

---

## 🐛 Problèmes Courants

### "OPENAI_API_KEY n'est pas configurée"
```bash
# Vérifier le .env
cd auditshield
notepad .env
# Ajoutez : OPENAI_API_KEY=sk-...
# Redémarrez Django et Celery
```

### "Cannot connect to redis"
```bash
# Lancer Redis
docker run -d -p 6379:6379 redis:alpine

# Vérifier
redis-cli ping
# Devrait retourner : PONG
```

### Task reste en "IA_RUNNING"
- Vérifiez que Celery tourne (Terminal 2)
- Consultez les logs Celery pour voir l'erreur

### Erreur OpenAI "Quota exceeded"
- Vérifiez votre compte : https://platform.openai.com/account/usage
- Ajoutez des crédits ou utilisez `gpt-3.5-turbo`

---

## 📖 Documentation Complète

Pour plus de détails, consultez :
- `TEST_KIT_IA_GUIDE.md` - Guide complet
- `IMPLEMENTATION_IA_GPT_KIT_COMPLET.md` - Architecture technique

---

## 💡 Commandes Utiles

### Vérifier la configuration
```bash
python manage.py shell
```
```python
import os
from django.conf import settings
print(f"API Key: {os.getenv('OPENAI_API_KEY')[:10]}...")
print(f"Model: {settings.OPENAI_CHAT_MODEL}")
```

### Voir les demandes de kit
```python
from store.models import ClientInquiry
kits = ClientInquiry.objects.filter(kind='KIT')
print(f"Total: {kits.count()}")
for kit in kits.filter(payment_status='PAID')[:5]:
    print(f"  #{kit.pk} - {kit.contact_name} - {kit.processing_state}")
```

### Voir les brouillons générés
```python
from store.models import GeneratedDraft
drafts = GeneratedDraft.objects.all()
for d in drafts:
    print(f"  Inquiry #{d.inquiry_id} - {d.model_name} - {d.token_usage} tokens")
```

---

**Besoin d'aide ?** Consultez `TEST_KIT_IA_GUIDE.md` pour le guide détaillé ! 📚

