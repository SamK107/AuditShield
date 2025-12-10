# 🚀 DÉMARRAGE RAPIDE - Système IA Kit Complet

## ⚡ Configuration en 5 Minutes

### 1️⃣ Clé OpenAI (2 min)

```bash
# 1. Obtenez votre clé sur : https://platform.openai.com/api-keys
# 2. Éditez le .env :
notepad C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield\.env
```

Ajoutez :
```
OPENAI_API_KEY=sk-votre-clé-complète-ici
OPENAI_CHAT_MODEL=gpt-4o-mini
```

Sauvegardez (Ctrl+S).

---

### 2️⃣ Redis (1 min)

**Option simple avec Docker :**
```bash
docker run -d -p 6379:6379 --name auditshield-redis redis:alpine
```

**Vérification :**
```bash
docker ps
# Vous devriez voir : auditshield-redis
```

---

### 3️⃣ Lancement (2 terminaux)

**Terminal 1 - Django :**
```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py runserver
```

**Terminal 2 - Celery :**
```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
celery -A config worker -l info
```

**Attendez ce message dans Terminal 2 :**
```
[INFO] celery@... ready.
```

✅ **Si vous voyez "ready", c'est bon !**

---

## 🧪 Test Rapide

### Créer une Demande de Test

**Terminal 3 (nouveau) :**
```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield
python manage.py shell
```

**Copiez-collez tout ce bloc :**
```python
from store.models import ClientInquiry, InquiryDocument
from django.core.files.base import ContentFile

# Supprimer les tests précédents (optionnel)
# ClientInquiry.objects.filter(email="test@example.com").delete()

inquiry = ClientInquiry.objects.create(
    kind="KIT",
    contact_name="Alice Martin",
    email="test@example.com",
    organization_name="Mairie de Bamako Centre",
    context_text="Administration publique, 80 agents, budget 200M FCFA/an",
    mission_text="Gestion des services municipaux et finances publiques",
    payment_status="PAID",
    processing_state="PAID"
)

doc_content = """RÈGLEMENT INTÉRIEUR - MAIRIE DE BAMAKO CENTRE

Article 1 - Organisation des services
La mairie est structurée en 5 services :
- Service des finances et du budget
- Service de l'urbanisme et de l'habitat
- Service de l'état civil
- Service des affaires sociales
- Service technique et logistique

Article 2 - Contrôle interne
Un audit interne est réalisé annuellement par le contrôleur municipal.
Un audit externe est requis tous les 2 ans.

Article 3 - Documents obligatoires
- Registre des délibérations (conservé 10 ans)
- Livre journal des recettes et dépenses
- Inventaire annuel du patrimoine
- Registres d'état civil
- Contrats et marchés publics

Article 4 - Gestion budgétaire
- Tout engagement >5000 FCFA nécessite un bon de commande
- Paiements >50000 FCFA nécessitent validation du maire
- Contrôle a priori sur dépenses >100000 FCFA

Article 5 - Passation des marchés
Les marchés publics >10M FCFA suivent la procédure d'appel d'offres.
"""

doc = InquiryDocument.objects.create(inquiry=inquiry, original_name="reglement_interieur.txt")
doc.file.save("reglement.txt", ContentFile(doc_content.encode()))

print()
print("=" * 70)
print("✅ DEMANDE DE TEST CRÉÉE !")
print("=" * 70)
print(f"ID : {inquiry.pk}")
print(f"Client : {inquiry.contact_name}")
print(f"Email : {inquiry.email}")
print(f"Documents : 1 fichier")
print()
print("🌐 Accédez à : http://localhost:8000/kit-complet-traitement/")
print()
print("👉 Cliquez sur 'Traiter avec l'IA' pour lancer la génération !")
print("=" * 70)

exit()
```

---

### Lancer le Traitement

1. **Ouvrez** : http://localhost:8000/kit-complet-traitement/
2. **Connectez-vous** comme staff/admin
3. **Trouvez** la ligne "Alice Martin"
4. **Cliquez** sur le bouton bleu **"Traiter avec l'IA"**

**Vous devriez voir :**
- Message vert : "Traitement IA lancé..."
- Statut : "IA_RUNNING" (orange)
- Spinner : "IA en cours…"

**Dans Terminal 2 (Celery) :**
```
[INFO] Task store.tasks.run_kit_ai_pipeline[...] received
[INFO] Extraction documents...
[INFO] Appel OpenAI...
[INFO] Génération réussie...
[INFO] Task succeeded in 42.3s
```

---

### Résultat (après 30-60 sec)

**Rafraîchissez la page** (F5)

**Vous devriez voir :**
- ✅ Statut : "DRAFT_DONE" (violet)
- ✅ Bouton : "Télécharger le brouillon" (vert)

**Cliquez sur "Télécharger le brouillon"**

**Le fichier Word téléchargé contiendra :**
```
# Kit complet de préparation à l'audit

## Introduction générale
Préparé pour : Alice Martin - Mairie de Bamako Centre
...

## Questionnaires de préparation

### Questions relatives au Règlement Intérieur
1. Le registre des délibérations est-il à jour et conservé conformément ?
2. Les 5 services sont-ils clairement définis avec des responsables ?
3. L'audit interne annuel est-il réalisé ?
...

## Tableaux d'irrégularités

| Irrégularité | Référence | Acteurs | Dispositions |
|--------------|-----------|---------|--------------|
| Absence de registre des délibérations | Art. 3 | Secrétaire général | Mettre en place... |
| Non-respect du seuil validation maire | Art. 4 | Service finances | Procédure... |
...

## Synthèse et recommandations
...

## Plan d'action
1. Vérifier registres obligatoires (Priorité haute)
2. Former les agents aux procédures (Priorité moyenne)
...
```

---

## 🎉 Succès !

Si vous avez téléchargé un document Word bien structuré :

### ✅ LE SYSTÈME FONCTIONNE À 100% !

**Vous pouvez maintenant :**
1. ✅ Tester avec vos documents réels
2. ✅ Ajuster les consignes si nécessaire
3. ✅ Former votre équipe
4. ✅ Mettre en production !

---

## 🆘 Problème ?

### Redis ne démarre pas
→ Consultez **`SETUP_REDIS.md`**

### OpenAI ne fonctionne pas
→ Consultez **`SETUP_OPENAI_KEY.md`**

### Autre problème
→ Consultez **`TEST_KIT_IA_GUIDE.md`** section "Troubleshooting"

---

## 📖 Documentation Complète

| Fichier | Contenu | Quand le lire ? |
|---------|---------|-----------------|
| **START_HERE.md** | Guide de démarrage | ✅ Maintenant ! |
| **SETUP_OPENAI_KEY.md** | Config OpenAI détaillée | Si problème API |
| **SETUP_REDIS.md** | Installation Redis | Si problème Celery |
| **QUICK_TEST_GUIDE.md** | Test rapide | Après config |
| **TEST_KIT_IA_GUIDE.md** | Guide complet | Pour tout comprendre |
| **IMPLEMENTATION_IA_GPT_KIT_COMPLET.md** | Architecture | Pour maintenance |

---

## 🎯 Checklist Complète

### Configuration
- [ ] Clé OpenAI dans `.env`
- [ ] Redis installé et démarré
- [ ] Packages Python installés

### Démarrage
- [ ] Django tourne (Terminal 1)
- [ ] Celery tourne (Terminal 2)
- [ ] Message "celery ready" affiché

### Test
- [ ] Demande de test créée
- [ ] Page accessible : `/kit-complet-traitement/`
- [ ] Clic "Traiter avec l'IA"
- [ ] Logs Celery visibles
- [ ] Brouillon téléchargé après 30-60s
- [ ] Document Word bien formaté

---

## 💡 Commandes de Référence Rapide

```bash
# Démarrer Redis (Docker)
docker start auditshield-redis

# Démarrer Django
cd auditshield && python manage.py runserver

# Démarrer Celery
cd auditshield && celery -A config worker -l info

# Shell Django (pour tests)
python manage.py shell

# Vérifier Redis
redis-cli ping  # ou : docker exec auditshield-redis redis-cli ping
```

---

## 🌟 Prêt à Commencer !

**Suivez simplement les étapes ci-dessus** et vous aurez un système IA fonctionnel en **5 minutes** ! ⏱️

**Bon test ! 🧪**

---

*Guide créé le 7 décembre 2025*  
*Système : AuditShield v1.0*

