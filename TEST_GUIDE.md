# 🧪 Guide de Test Rapide

## Démarrage

```powershell
cd C:\Users\Lenovo X1Yoga\Documents\AUDITSHIELD-DEV\auditshield
..\. venv\Scripts\Activate.ps1
python manage.py runserver
```

---

## ✅ Test 1 : Page "Autres moyens d'achat" (NOUVEAU DESIGN)

### URL
```
http://127.0.0.1:8000/buy/other-methods/produit/
```

### Ce que vous devez voir

#### Header
```
╔════════════════════════════════════════════════╗
║  Choisissez votre plateforme d'achat          ║
║  Achetez l'ebook sur la plateforme de votre   ║
║  choix. Toutes les transactions...            ║
╚════════════════════════════════════════════════╝
```

#### Bandeau info (bleu)
```
╔════════════════════════════════════════════════╗
║ 💡 Accès aux bonus inclus                     ║
║    Après votre achat, l'ebook contient des    ║
║    liens sécurisés vers vos bonus...          ║
╚════════════════════════════════════════════════╝
```

#### 3 Cards (1 ligne sur desktop, responsive)
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ [🔲] Publiseer│ │ [🔲] YouScribe│ │ [🔲] Chariow │
│ ✓ Recommandé │ │              │ │              │
│              │ │              │ │              │
│ Distribution │ │ Portée       │ │ Extension    │
│ mondiale...  │ │ Afrique...   │ │ régionale    │
│              │ │              │ │              │
│ ✓ Sécurisé   │ │ ✓ Sécurisé   │ │ ✓ Sécurisé   │
│ ⚡ Instantané │ │ ⚡ Instantané │ │ ⚡ Instantané │
│              │ │              │ │              │
│ [Acheter →]  │ │ [Acheter →]  │ │ [Acheter →]  │
└──────────────┘ └──────────────┘ └──────────────┘
```

### ✅ Checklist
- [ ] **Exactement 3 cards** (pas 4, Selar est supprimé)
- [ ] **Publiseer a le badge "Recommandé"** (vert)
- [ ] **Hover sur une card** → bordure devient bleue + shadow
- [ ] **Logos visibles** dans des conteneurs carrés
- [ ] **Boutons pleine largeur** avec flèche →
- [ ] **Responsive** : 1 colonne mobile, 2 tablette, 3 desktop

---

## ✅ Test 2 : Layout Global (pages normales)

### URL
```
http://127.0.0.1:8000/offres/
```

### Ce que vous devez voir

#### Header (sticky, bleu)
```
╔════════════════════════════════════════════════╗
║ [Logo] Bloom Shield Gouvernance   [Menu]      ║
║        Offres | Exemples | À propos           ║
╚════════════════════════════════════════════════╝
```

#### Footer
```
╔════════════════════════════════════════════════╗
║ © 2025 Bloom Shield Gouvernance               ║
║ Mentions légales | Confidentialité | Cookies  ║
╚════════════════════════════════════════════════╝
```

### ✅ Checklist
- [ ] **Header présent** avec logo et navigation
- [ ] **Footer présent** avec copyright et liens légaux
- [ ] **Layout identique** sur toutes les pages
- [ ] **Assets chargés** (CSS, JS, icônes Lucide)

---

## ✅ Test 3 : Pages d'erreur robustes

### Configuration requise
Éditer `config/settings/dev.py` :
```python
DEBUG = False  # ⚠️ Temporaire pour test
```

### Test 404

#### URL
```
http://127.0.0.1:8000/cette-page-nexiste-pas/
```

#### Ce que vous devez voir
```
╔════════════════════════════════════════════════╗
║ [Header avec logo]                             ║
╠════════════════════════════════════════════════╣
║                                                ║
║   🔍 Oups — page introuvable                  ║
║                                                ║
║   Le contenu demandé n'existe pas ou n'est    ║
║   plus disponible.                             ║
║                                                ║
║   [Retour à l'accueil]  [Voir les offres]     ║
║                                                ║
╠════════════════════════════════════════════════╣
║ [Footer simplifié avec liens hardcodés]       ║
╚════════════════════════════════════════════════╝
```

### Test 500

#### URL
```
http://127.0.0.1:8000/boom/
```

#### Ce que vous devez voir
```
╔════════════════════════════════════════════════╗
║ [Header avec logo]                             ║
╠════════════════════════════════════════════════╣
║                                                ║
║   💥 Une erreur est survenue                  ║
║                                                ║
║   Désolé, un incident technique s'est         ║
║   produit. L'équipe a été informée.           ║
║                                                ║
║   [Retour à l'accueil]                        ║
║                                                ║
╠════════════════════════════════════════════════╣
║ [Footer simplifié avec liens hardcodés]       ║
╚════════════════════════════════════════════════╝
```

### ✅ Checklist pages d'erreur
- [ ] **404 s'affiche** sur URL inexistante
- [ ] **500 s'affiche** sur `/boom/`
- [ ] **Design élégant** (pas la page Django par défaut)
- [ ] **Header et footer présents**
- [ ] **Liens fonctionnent** (même si URLconf cassée)
- [ ] **Icônes Lucide s'affichent**

### ⚠️ Remettre DEBUG=True après test
```python
# config/settings/dev.py
DEBUG = True  # Remettre à True après test
```

---

## ✅ Test 4 : Formulaire Bonus

### URL
```
http://127.0.0.1:8000/bonus/kit-preparation/start
```

### Ce que vous devez voir

#### Checkbox
```
☐ Acheté via une plateforme externe (Publiseer / YouScribe / Chariow)
```

**⚠️ Ne doit PAS mentionner "Selar"**

### ✅ Checklist
- [ ] Texte ne mentionne **pas Selar**
- [ ] Liste les 3 plateformes restantes
- [ ] Formulaire fonctionne correctement

---

## ✅ Test 5 : Admin Django

### URL
```
http://127.0.0.1:8000/admin/downloads/externalentitlement/
```

### Ce que vous devez voir

#### Champ "Platform" (dropdown)
```
Plateforme :
  [ v ]
  ─────────
  Publiseer
  YouScribe Afrique
  Chariow
  Autre
  ─────────
```

**⚠️ "Selar" ne doit PAS apparaître dans la liste**

### ✅ Checklist
- [ ] Dropdown ne contient **pas "Selar"**
- [ ] 4 options disponibles (Publiseer, YouScribe, Chariow, Autre)
- [ ] Anciennes entrées "Selar" affichent maintenant "Autre"

---

## 🎨 Test Responsive (Design)

### Desktop (> 1024px)
```
[Publiseer]  [YouScribe]  [Chariow]
   ↓             ↓            ↓
3 colonnes alignées
```

### Tablette (768px - 1024px)
```
[Publiseer]  [YouScribe]
     ↓            ↓
[Chariow]
     ↓
2 colonnes puis 1
```

### Mobile (< 768px)
```
[Publiseer]
     ↓
[YouScribe]
     ↓
[Chariow]
     ↓
1 colonne empilée
```

### ✅ Checklist responsive
- [ ] Desktop : 3 colonnes côte à côte
- [ ] Tablette : 2 colonnes
- [ ] Mobile : 1 colonne empilée
- [ ] Cards **même hauteur** sur chaque ligne
- [ ] Boutons bien alignés

---

## 🐛 Dépannage

### Problème : "Missing staticfiles manifest entry"
**Solution** :
```bash
.venv\Scripts\python.exe auditshield\manage.py collectstatic --noinput
```

### Problème : Pages d'erreur ne s'affichent pas
**Solution** :
- Vérifier `DEBUG=False` dans settings
- Vérifier `ALLOWED_HOSTS` inclut `'127.0.0.1'`
- Vérifier `handler404` et `handler500` dans `urls.py`

### Problème : Selar apparaît encore
**Solution** :
- Vider le cache du navigateur (Ctrl+F5)
- Relancer le serveur Django
- Re-exécuter `collectstatic`

### Problème : Cards pas alignées
**Solution** :
- Vérifier Tailwind CSS est chargé
- Vérifier `app.build.css` existe dans staticfiles
- F12 → Console → vérifier erreurs JS/CSS

---

## 📸 Captures d'écran recommandées

Prendre des captures pour documentation :
1. ✅ Page `/buy/other-methods/produit/` (desktop)
2. ✅ Page `/buy/other-methods/produit/` (mobile)
3. ✅ Hover sur une card (effet bordure bleue)
4. ✅ Page 404 personnalisée
5. ✅ Page 500 personnalisée

---

## 🎯 Critères de succès

### La session est réussie si :

#### Fonctionnel
- [x] Aucune erreur au démarrage du serveur
- [ ] Toutes les pages se chargent correctement
- [ ] Formulaires fonctionnent
- [ ] Migrations appliquées

#### Visuel
- [ ] Design moderne et professionnel
- [ ] 3 plateformes affichées (pas 4)
- [ ] Badge "Recommandé" sur Publiseer
- [ ] Effets hover fonctionnent
- [ ] Responsive impeccable

#### Technique
- [x] Aucune référence à Selar dans le code actif
- [x] Migration de données réussie
- [x] Collectstatic sans erreur
- [ ] Pages d'erreur robustes testées

#### Documentation
- [x] 10 fichiers de documentation créés
- [x] Guides complets et détaillés
- [x] Instructions de test claires
- [x] Checklist de production

---

## 🚀 Validation finale

Si **tous les tests passent** :
1. ✅ Remettre `DEBUG=True` dans dev.py
2. ✅ Supprimer `/boom/` de core/urls.py
3. ✅ Supprimer `boom()` de core/views.py
4. ✅ Commit les changements
5. ✅ Prêt pour production !

---

*Guide de test créé le 21 octobre 2025*
*Suivez ce guide pour valider toutes les modifications*
*Temps estimé : 15-20 minutes*

