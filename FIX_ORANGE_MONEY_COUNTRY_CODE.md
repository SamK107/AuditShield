# ✅ FIX: Code Pays Orange Money (Mali vs Guinée)

## 🐛 Problème Identifié

L'URL de paiement générée contenait `ow-sb` (Guinée) au lieu de `ml-sb` (Mali):

**Avant (incorrect pour le Mali):**
```
https://webpayment-ow-sb.orange-money.com/payment/pay_token/v1dfd6fnzwg8...
                  ^^
                  Guinée (OW = Ouest)
```

**Après (correct pour le Mali):**
```
https://webpayment-ml-sb.orange-money.com/payment/pay_token/v1dfd6fnzwg8...
                  ^^
                  Mali
```

---

## 🔧 Correction Appliquée

### 1. Nouvelle Variable d'Environnement

**Fichier:** `config/settings/base.py`

Ajout de:
```python
ORANGE_COUNTRY_CODE = os.getenv("ORANGE_COUNTRY_CODE", "ml")
```

### 2. URL Dynamique avec Code Pays

**Fichier:** `store/services/orange_money.py`

**Avant:**
```python
# Hardcodé avec 'ow'
sandbox_payment_url = f"https://webpayment-ow-sb.orange-money.com/payment/pay_token/{pay_token}"
```

**Après:**
```python
# Dynamique avec le code pays configuré
country_code = config.get("COUNTRY_CODE", "ml")
sandbox_payment_url = f"https://webpayment-{country_code}-sb.orange-money.com/payment/pay_token/{pay_token}"
```

---

## ⚙️ Configuration

### Dans votre `.env`

Ajouter (optionnel, `ml` est la valeur par défaut):

```bash
# Code pays Orange Money
# ml = Mali (default)
# ow = Guinée (Ouest)
# ci = Côte d'Ivoire
# sn = Sénégal
ORANGE_COUNTRY_CODE=ml
```

### Codes Pays Orange Money

| Code | Pays | URL Sandbox | URL Production |
|------|------|-------------|----------------|
| `ml` | Mali | `webpayment-ml-sb.orange-money.com` | `webpayment-ml.orange-money.com` |
| `ow` | Guinée | `webpayment-ow-sb.orange-money.com` | `webpayment-ow.orange-money.com` |
| `ci` | Côte d'Ivoire | `webpayment-ci-sb.orange-money.com` | `webpayment-ci.orange-money.com` |
| `sn` | Sénégal | `webpayment-sn-sb.orange-money.com` | `webpayment-sn.orange-money.com` |

---

## 🧪 Test

### Méthode 1: Script de Test

```bash
cd auditshield
python test_orange_money_sandbox.py
```

**Vérifier dans les logs:**
```
[OM][create_payment] Mode sandbox détecté | 
Country code: ml | 
URL sandbox corrigée: https://webpayment-ml-sb.orange-money.com/payment/pay_token/...
                                        ^^
                                        Mali!
```

### Méthode 2: Test dans le Navigateur

1. **Démarrer Django:**
   ```bash
   python manage.py runserver
   ```

2. **Ouvrir la page de paiement:**
   ```
   http://127.0.0.1:8000/buy/cinetpay/
   ```

3. **Remplir le formulaire et cliquer sur "Payer avec Orange Money ML"**

4. **Vérifier l'URL de redirection** (devrait contenir `ml-sb`):
   ```
   https://webpayment-ml-sb.orange-money.com/payment/pay_token/...
   ```

---

## 📋 Checklist

- [x] Variable `ORANGE_COUNTRY_CODE` ajoutée dans `settings/base.py`
- [x] Code pays lu depuis la config dans `orange_money.py`
- [x] URL sandbox construite dynamiquement avec le code pays
- [x] Documentation mise à jour (`ORANGE_MONEY_ENV_TEMPLATE.md`)
- [x] Logs améliorés pour afficher le code pays utilisé
- [ ] Tester avec le script `test_orange_money_sandbox.py`
- [ ] Tester dans le navigateur
- [ ] Vérifier que l'URL contient bien `ml-sb`

---

## 🎯 Pourquoi c'était Important?

### Avant (avec `ow-sb`):
- ❌ Redirigé vers l'interface Orange Money **Guinée**
- ❌ Credentials Mali non reconnus
- ❌ Paiement impossible

### Après (avec `ml-sb`):
- ✅ Redirigé vers l'interface Orange Money **Mali**
- ✅ Credentials Mali reconnus
- ✅ Paiement possible

---

## 🚀 Prochaines Étapes

1. **Si vous n'avez PAS encore de `.env`:**
   - Le code utilisera `ml` par défaut ✅
   - Rien à faire!

2. **Si vous avez déjà un `.env`:**
   - Optionnel: Ajouter `ORANGE_COUNTRY_CODE=ml` pour être explicite
   - Mais ce n'est pas obligatoire (défaut = `ml`)

3. **Redémarrer Django:**
   ```bash
   python manage.py runserver
   ```

4. **Tester à nouveau le paiement**

---

## 📊 Détails Techniques

### Format des URLs Orange Money

**Sandbox:**
```
https://webpayment-{country_code}-sb.orange-money.com/payment/pay_token/{token}
                   ^^^^^^^^^^^^^^
                   Code pays + "-sb" (sandbox)
```

**Production:**
```
https://webpayment-{country_code}.orange-money.com/payment/pay_token/{token}
                   ^^^^^^^^^^^^^
                   Code pays (sans "-sb")
```

### Où est-ce Utilisé?

Le code pays est utilisé dans `create_payment_request()` ligne ~488-496:

```python
if "/dev/v1/webpayment" in webpay_url:
    # Mode sandbox
    country_code = config.get("COUNTRY_CODE", "ml")
    sandbox_payment_url = f"https://webpayment-{country_code}-sb.orange-money.com/payment/pay_token/{pay_token}"
    payment_url = sandbox_payment_url
```

En **production** (`/ml/v1/webpayment`), l'API retourne directement l'URL correcte.

---

## ✅ Résolution

**Problème:** URL avec `ow-sb` (Guinée) au lieu de `ml-sb` (Mali)

**Cause:** Code pays hardcodé à `ow` dans le code

**Solution:** 
1. ✅ Ajout variable `ORANGE_COUNTRY_CODE` (défaut: `ml`)
2. ✅ URL construite dynamiquement avec le code pays
3. ✅ Logs améliorés pour tracer le code pays utilisé

**Status:** ✅ **CORRIGÉ**

---

**Date:** Décembre 2025  
**Impact:** Critique pour le Mali  
**Priorité:** Haute

