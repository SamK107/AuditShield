# 🔑 Configuration de la Clé API OpenAI

## Étape 1 : Obtenir une Clé API OpenAI

### Option A : Si vous avez déjà un compte OpenAI

1. **Allez sur** : https://platform.openai.com/api-keys
2. **Connectez-vous** avec votre compte OpenAI
3. **Cliquez sur** "Create new secret key"
4. **Donnez un nom** : "AuditShield-Production" ou "AuditShield-Dev"
5. **Copiez la clé** (elle commence par `sk-...`)
   ⚠️ **Important** : Elle ne sera plus jamais affichée, copiez-la immédiatement !
6. **Sauvegardez-la** dans un endroit sûr (gestionnaire de mots de passe)

### Option B : Si vous n'avez pas de compte OpenAI

1. **Allez sur** : https://platform.openai.com/signup
2. **Créez un compte** avec votre email
3. **Vérifiez votre email**
4. **Ajoutez une méthode de paiement** : https://platform.openai.com/account/billing/payment-methods
   - Carte bancaire recommandée
   - Minimum requis : ~$5 pour commencer
5. **Suivez "Option A"** ci-dessus pour créer la clé

### Option C : Utiliser les crédits gratuits (nouveaux comptes)

OpenAI offre parfois **$5 de crédits gratuits** pour les nouveaux comptes.
- Vérifiez sur : https://platform.openai.com/account/usage
- Ces crédits permettent de tester le système (~100-200 kits)

---

## Étape 2 : Configurer la Clé dans AuditShield

### Méthode 1 : Via le fichier `.env` (Recommandé)

1. **Ouvrez le fichier `.env`** dans le dossier `auditshield/` :
   ```bash
   notepad C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield\.env
   ```

2. **Cherchez la ligne** `OPENAI_API_KEY=` (ou ajoutez-la si absente)

3. **Remplacez** par votre clé :
   ```bash
   OPENAI_API_KEY=sk-votre-clé-ici-complète
   ```

4. **Ajoutez aussi** (si absent) :
   ```bash
   # Modèle à utiliser (gpt-4o-mini est le moins cher)
   OPENAI_CHAT_MODEL=gpt-4o-mini
   
   # Si vous avez accès à GPT-4.1-mini ou GPT-4o :
   # OPENAI_CHAT_MODEL=gpt-4.1-mini
   # OPENAI_CHAT_MODEL=gpt-4o
   ```

5. **Sauvegardez** (Ctrl+S) et **fermez** l'éditeur

### Méthode 2 : Via l'éditeur de code (VSCode, etc.)

1. **Ouvrez le projet** dans votre éditeur
2. **Naviguez vers** `auditshield/.env`
3. **Ajoutez/modifiez** :
   ```
   OPENAI_API_KEY=sk-votre-clé-complète
   OPENAI_CHAT_MODEL=gpt-4o-mini
   ```
4. **Sauvegardez**

---

## Étape 3 : Vérification

### Vérifier que Django charge la clé

```bash
cd "C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV"
.\.venv\Scripts\Activate.ps1
cd auditshield

# Commande de vérification
python manage.py shell
```

Dans le shell Python :
```python
import os
from django.conf import settings

# Vérifier la clé
api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', '')
if api_key:
    print(f"✅ Clé OpenAI configurée : {api_key[:10]}...{api_key[-4:]}")
else:
    print("❌ Clé OpenAI MANQUANTE")

# Vérifier le modèle
model = getattr(settings, 'OPENAI_CHAT_MODEL', 'N/A')
print(f"✅ Modèle : {model}")

exit()
```

**Résultat attendu :**
```
✅ Clé OpenAI configurée : sk-proj-a...Xy2z
✅ Modèle : gpt-4o-mini
```

### Test de connexion OpenAI (Optionnel)

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Test simple
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Dis bonjour en français"}],
        max_tokens=50
    )
    print(f"✅ OpenAI fonctionne : {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Erreur : {e}")

exit()
```

---

## 🔐 Sécurité de la Clé

### ✅ Bonnes Pratiques

1. **Ne JAMAIS commiter** le fichier `.env` dans Git
   - Vérifiez que `.env` est dans `.gitignore`
   - Créez un `.env.example` sans la vraie clé

2. **Limiter les permissions** de la clé sur OpenAI :
   - Allez sur https://platform.openai.com/api-keys
   - Cliquez sur votre clé → "Permissions"
   - Limitez l'accès aux modèles nécessaires

3. **Monitorer l'utilisation** :
   - https://platform.openai.com/account/usage
   - Configurez des alertes de budget

4. **Rotation régulière** :
   - Changez la clé tous les 3-6 mois
   - Révoquez les anciennes clés

### ⚠️ Si votre clé est compromise

1. **Révocation immédiate** :
   - https://platform.openai.com/api-keys
   - Cliquez sur la clé → "Revoke"

2. **Créez une nouvelle clé**

3. **Mettez à jour** `.env` avec la nouvelle clé

---

## 💰 Gestion des Coûts

### Tarifs GPT-4o-mini (Décembre 2024)

- **Input** : $0.15 / 1M tokens (~150 tokens = 100 mots)
- **Output** : $0.60 / 1M tokens

**Estimation par kit :**
- Input : 3000-8000 tokens (~$0.0005-0.0012)
- Output : 2000-5000 tokens (~$0.0012-0.0030)
- **Total : ~$0.001-0.004 par kit** (0.1 à 0.4 centimes)

### Budget Mensuel Recommandé

- **50 kits/mois** : ~$0.20
- **200 kits/mois** : ~$0.80
- **1000 kits/mois** : ~$4.00

💡 **GPT-4o-mini est 10-20x moins cher que GPT-4** !

### Configurer un Budget Limit

1. **Allez sur** : https://platform.openai.com/account/billing/limits
2. **Soft limit** : Alerte par email (ex: $10)
3. **Hard limit** : Blocage automatique (ex: $50)

### Monitorer en Temps Réel

```python
# Dans le shell Django
from store.models import GeneratedDraft

# Voir l'utilisation
drafts = GeneratedDraft.objects.all()
total_tokens = sum(d.token_usage or 0 for d in drafts)
print(f"Total tokens utilisés : {total_tokens:,}")

# Estimation coût (GPT-4o-mini)
input_cost = (total_tokens * 0.5) * (0.15 / 1_000_000)  # 50% input
output_cost = (total_tokens * 0.5) * (0.60 / 1_000_000) # 50% output
total_cost = input_cost + output_cost
print(f"Coût estimé : ${total_cost:.2f}")
```

---

## 🎯 Modèles Disponibles

### Recommandés pour AuditShield

| Modèle | Prix (input/output) | Qualité | Vitesse | Recommandation |
|--------|---------------------|---------|---------|----------------|
| **gpt-4o-mini** | $0.15 / $0.60 | Très bonne | Rapide | ⭐ **Recommandé** |
| gpt-3.5-turbo | $0.50 / $1.50 | Bonne | Très rapide | Budget serré |
| gpt-4o | $2.50 / $10.00 | Excellente | Rapide | Kits premium |
| gpt-4-turbo | $10 / $30 | Excellente | Moyen | Overkill |

**Notre choix par défaut : `gpt-4o-mini`**
- Excellent rapport qualité/prix
- Suffisant pour générer des kits professionnels
- 20x moins cher que GPT-4

---

## 🔄 Changer de Modèle

### Dans le `.env` :

```bash
# Option 1 : GPT-4o-mini (Recommandé - Moins cher)
OPENAI_CHAT_MODEL=gpt-4o-mini

# Option 2 : GPT-3.5-turbo (Budget minimal)
OPENAI_CHAT_MODEL=gpt-3.5-turbo

# Option 3 : GPT-4o (Qualité maximale)
OPENAI_CHAT_MODEL=gpt-4o
```

Redémarrez Django et Celery après modification.

---

## 🐛 Dépannage

### Erreur : "Invalid API key"

**Cause :** Clé mal copiée ou révoquée

**Solution :**
1. Vérifiez le `.env` (pas d'espace avant/après la clé)
2. Vérifiez sur https://platform.openai.com/api-keys que la clé est active
3. Créez une nouvelle clé si nécessaire

### Erreur : "Quota exceeded"

**Cause :** Limite de budget atteinte

**Solution :**
1. Vérifiez : https://platform.openai.com/account/usage
2. Ajoutez des crédits ou augmentez la limite
3. Temporairement, utilisez `gpt-3.5-turbo` (moins cher)

### Erreur : "Model not found"

**Cause :** Accès au modèle non autorisé

**Solution :**
1. Vérifiez votre plan OpenAI
2. Utilisez `gpt-4o-mini` (accessible à tous)
3. Attendez si compte très récent (délai d'activation)

### La clé ne se charge pas

**Cause :** Django ne lit pas le `.env`

**Solution :**
```bash
# Vérifier que python-dotenv est installé
pip list | Select-String dotenv

# Si absent :
pip install python-dotenv

# Redémarrer Django
```

---

## ✅ Checklist Finale

Avant de passer à l'installation de Redis :

- [ ] Compte OpenAI créé
- [ ] Clé API générée (commence par `sk-...`)
- [ ] Clé ajoutée dans `.env`
- [ ] Modèle configuré (`OPENAI_CHAT_MODEL=gpt-4o-mini`)
- [ ] Vérification réussie dans le shell Django
- [ ] Budget configuré sur OpenAI (optionnel mais recommandé)

---

**Prêt ? Passons à l'installation de Redis ! →**

Consultez **`SETUP_REDIS.md`** pour la suite.

