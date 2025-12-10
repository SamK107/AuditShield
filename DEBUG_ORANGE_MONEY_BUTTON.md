# 🐛 Debug: Bouton Orange Money ML ne fonctionne pas

## Problème
Quand vous cliquez sur "Payer avec Orange Money ML" sur `/buy/cinetpay/`, rien ne se passe.

## Modifications Apportées

### 1. Ajout de l'affichage des messages d'erreur ✅
**Fichier:** `store/templates/store/buy_cinetpay.html`

Ajout d'un bloc pour afficher les messages Django (erreurs, succès, etc.) au début du formulaire.

### 2. Changement de la valeur du bouton Orange Money ✅
**Avant:** `value="orange"`  
**Après:** `value="orange_money_ml"`

Cela correspond mieux au code dans `payment_views.py`:
```python
if provider_key in ("orange", "orange_money_ml"):
```

### 3. Ajout de debug JavaScript ✅
Script qui log dans la console du navigateur:
- Quel bouton est cliqué
- Si le formulaire est valide
- Quels champs requis sont vides
- Les données envoyées lors du submit

### 4. Ajout de logs côté serveur ✅
**Fichier:** `store/payment_views.py`

Ajout de logs dans `start_checkout()`:
- Méthode HTTP
- Slug du produit
- Provider sélectionné
- Données POST complètes

---

## Comment Debugger

### Étape 1: Vérifier la Console JavaScript

1. Ouvrir la page: `http://127.0.0.1:8000/buy/cinetpay/`
2. Ouvrir la console du navigateur (F12 → Console)
3. Remplir le formulaire (tous les champs requis!)
4. Cliquer sur "Payer avec Orange Money ML"

**Résultat attendu dans la console:**
```
[DEBUG] Bouton cliqué: orange_money_ml
[DEBUG] Formulaire valide: true
[DEBUG] Tous les champs requis sont remplis
[DEBUG] Formulaire soumis avec données:
  csrfmiddlewaretoken: xxxx
  last_name: Dupont
  first_name: Jean
  email: test@example.com
  phone: 77011011234
  tier_id: 
  provider: orange_money_ml
```

**Si vous voyez des erreurs:**
- `Formulaire valide: false` → Remplir tous les champs requis (nom, prénom, email)
- `Champs requis vides: [...]` → Liste des champs à remplir

### Étape 2: Vérifier les Logs Django

Dans le terminal où Django tourne, chercher les logs:

```bash
# Logs dans le terminal
[start_checkout] Request method: POST
[start_checkout] Product slug: cinetpay
[start_checkout] Provider key: orange_money_ml
[start_checkout] POST data: {...}
```

**Si les logs n'apparaissent pas:**
- Le formulaire ne se soumet pas (voir Étape 1)
- Vérifier que `DJANGO_DEBUG=True` dans `.env`

**Si vous voyez les logs mais avec `provider_key: cinetpay`:**
- Le bouton Orange Money ne passe pas le bon paramètre
- Vérifier le HTML du formulaire

### Étape 3: Vérifier les Logs Orange Money

```bash
tail -f logs/orange_money.log
```

**Résultat attendu après clic sur Orange Money:**
```
[OM][start_checkout] API response - payment_url: https://..., pay_token: xxx
ORANGE_WEBPAY_REQUEST | OAuth Token | url=...
ORANGE_WEBPAY_RESPONSE | OAuth Token | status=200
ORANGE_WEBPAY_REQUEST | WebPayment Init | url=...
ORANGE_WEBPAY_RESPONSE | WebPayment Init | status=201
```

**Si vous voyez une erreur:**
- Vérifier que les credentials Orange Money sont configurés dans `.env`
- Voir la section Troubleshooting ci-dessous

### Étape 4: Vérifier que les Variables Orange Money sont Configurées

```bash
cd auditshield/
python test_orange_money_sandbox.py
```

**Résultat attendu:**
```
✅ Configuration valide
✅ Token obtenu avec succès!
✅ Paiement initialisé avec succès!
```

**Si erreur "Variables manquantes":**
- Configurer `ORANGE_CLIENT_ID`, `ORANGE_CLIENT_SECRET`, `ORANGE_MERCHANT_KEY` dans `.env`
- Voir `ORANGE_MONEY_ENV_TEMPLATE.md`

---

## Causes Possibles

### 1. Champs Requis Non Remplis ❌
**Symptôme:** Rien ne se passe quand on clique sur le bouton

**Solution:**
- Remplir **tous** les champs requis: Nom, Prénom, Email
- Le champ Téléphone est optionnel

### 2. Erreur JavaScript ❌
**Symptôme:** Console montre des erreurs JS

**Solution:**
- Vérifier la console (F12)
- Désactiver les extensions de navigateur (AdBlock, etc.)
- Essayer dans un autre navigateur

### 3. Credentials Orange Money Manquants ❌
**Symptôme:** Erreur "Variables manquantes dans .env"

**Solution:**
```bash
# Ajouter dans .env
ORANGE_CLIENT_ID=your-client-id
ORANGE_CLIENT_SECRET=your-client-secret
ORANGE_MERCHANT_KEY=your-merchant-key
```

### 4. Erreur d'Authentification OAuth ❌
**Symptôme:** Logs montrent "Erreur OAuth"

**Solution:**
- Vérifier `ORANGE_CLIENT_ID` et `ORANGE_CLIENT_SECRET`
- Vérifier que l'application est "Active" sur https://developer.orange.com/

### 5. Erreur API Orange Money ❌
**Symptôme:** Logs montrent "Erreur API Orange Money (code XXX)"

**Solution:**
- Vérifier `ORANGE_MERCHANT_KEY`
- Consulter `logs/orange_money.log` pour plus de détails
- Contacter le support Orange Money si le problème persiste

---

## Test Rapide

Pour tester rapidement si Orange Money fonctionne:

```bash
# 1. Vérifier la config
cd auditshield/
python test_orange_money_sandbox.py

# 2. Lancer Django
python manage.py runserver

# 3. Ouvrir dans le navigateur
http://127.0.0.1:8000/buy/cinetpay/

# 4. Remplir le formulaire
Nom: Test
Prénom: User
Email: test@example.com
Téléphone: (optionnel)

# 5. Cliquer sur "Payer avec Orange Money ML"

# 6. Vérifier les logs
# Terminal Django: voir [start_checkout] logs
# Console navigateur: voir [DEBUG] logs
```

---

## Checklist de Debug

- [ ] Console JavaScript ouverte (F12)
- [ ] Tous les champs requis remplis (Nom, Prénom, Email)
- [ ] Logs Django activés (voir terminal)
- [ ] Variables Orange Money configurées dans `.env`
- [ ] Script `test_orange_money_sandbox.py` réussi
- [ ] Aucune erreur JavaScript dans la console
- [ ] Django tourne sans erreur (`python manage.py runserver`)

---

## Si Rien ne Fonctionne

1. **Redémarrer Django:**
   ```bash
   # Ctrl+C pour arrêter
   python manage.py runserver
   ```

2. **Vider le cache:**
   ```bash
   python manage.py collectstatic --clear --noinput
   ```

3. **Vérifier les migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Tester avec CinetPay:**
   - Si CinetPay fonctionne mais pas Orange Money → Problème de configuration Orange Money
   - Si ni CinetPay ni Orange Money ne fonctionnent → Problème de formulaire général

5. **Consulter les logs complets:**
   ```bash
   # Logs Orange Money
   cat logs/orange_money.log
   
   # Logs généraux
   cat logs/app.log
   ```

---

## Contact & Support

Si le problème persiste après avoir suivi ce guide:

1. Copier les logs de la console JavaScript
2. Copier les logs de Django (terminal)
3. Copier les logs Orange Money (`logs/orange_money.log`)
4. Noter les étapes exactes pour reproduire le problème

**Documentation:**
- Guide complet: `ORANGE_MONEY_INTEGRATION_COMPLETE.md`
- Variables env: `ORANGE_MONEY_ENV_TEMPLATE.md`
- Démarrage rapide: `QUICK_START_ORANGE_MONEY.md`

---

**Mise à jour:** Décembre 2025

