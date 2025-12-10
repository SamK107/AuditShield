# 🐛 DEBUG: Orange Money URL Problem

## ❌ Problème: DNS_PROBE_FINISHED_NXDOMAIN

L'URL `webpayment-ml-sb.orange-money.com` **n'existe pas**!

```
DNS_PROBE_FINISHED_NXDOMAIN
```

## 🔍 Analyse

### Ce que j'ai découvert:

1. ✅ `webpayment-ow-sb.orange-money.com` existe (Guinée/Ouest)
2. ❌ `webpayment-ml-sb.orange-money.com` n'existe PAS (Mali)

### Erreur dans ma correction:

J'ai supposé que chaque pays avait son propre domaine:
- `webpayment-ml-sb.orange-money.com` (Mali) ❌ N'EXISTE PAS
- `webpayment-ow-sb.orange-money.com` (Guinée) ✅ Existe
- `webpayment-ci-sb.orange-money.com` (Côte d'Ivoire) ❓ Inconnu

**Mais c'était faux!**

---

## ✅ Solution Correcte

**Ne PAS reconstruire l'URL nous-mêmes!**

L'API Orange Money **retourne déjà l'URL correcte** dans sa réponse:

```json
{
  "status": "SUCCESS",
  "pay_token": "dd497bda3b250e536186fc0663f32f40",
  "payment_url": "https://webpayment-ow-sb.orange-money.com/payment/pay_token/dd497bda..."
}
```

**Il faut utiliser cette URL telle quelle!**

---

## 🔧 Correction Appliquée

**Fichier:** `store/services/orange_money.py`

**Changement:**
```python
# AVANT (MAUVAIS): Je reconstruisais l'URL
country_code = config.get("COUNTRY_CODE", "ml")
payment_url = f"https://webpayment-{country_code}-sb.orange-money.com/payment/pay_token/{pay_token}"

# APRÈS (BON): J'utilise l'URL retournée par l'API
payment_url = result.get("payment_url")  # L'API sait quelle URL utiliser!
```

---

## 🧪 Tester Maintenant

### Étape 1: Vérifier Ce Que l'API Retourne

**Lancer le script de test:**
```bash
cd auditshield
python test_orange_money_sandbox.py
```

**Regarder les logs** pour voir `payment_url` dans la réponse:
```
ORANGE_WEBPAY_RESPONSE | WebPayment Init | 
status=201 | 
body={
  "status": "SUCCESS",
  "pay_token": "dd497bda...",
  "payment_url": "https://webpayment-???-sb.orange-money.com/..."
                              ^^^
                              Quelle URL l'API retourne-t-elle?
}
```

### Étape 2: Si l'API ne Retourne Pas d'URL

Si `payment_url` est vide ou null dans la réponse, l'API attend peut-être que vous construisiez l'URL vous-même avec `pay_token`.

**Dans ce cas, vérifier la documentation Orange Money Mali:**
- Quelle est l'URL correcte pour le sandbox Mali?
- Est-ce `webpayment-ow-sb.orange-money.com` (partagé)?
- Ou une autre URL spécifique au Mali?

---

## 📋 Questions à Répondre

Pour résoudre définitivement le problème, nous devons savoir:

### Question 1: Que retourne l'API?

Lancer `python test_orange_money_sandbox.py` et copier ici la réponse complète:

```json
{
  "status": "...",
  "pay_token": "...",
  "payment_url": "...",  <-- C'est quoi exactement?
  "notif_token": "..."
}
```

### Question 2: Documentation Orange Money Mali

Selon la documentation officielle Orange Money pour le **Mali**:
- Quelle est l'URL du sandbox pour les paiements?
- Est-ce différent de la Guinée (`ow-sb`)?

---

## 🔬 Debug Détaillé

### Activer les Logs Complets

**1. Ouvrir un terminal:**
```bash
cd auditshield
python manage.py runserver
```

**2. Dans un autre terminal, surveiller les logs:**
```bash
tail -f logs/orange_money.log
```

**3. Dans le navigateur:**
- Ouvrir `http://127.0.0.1:8000/buy/cinetpay/`
- Remplir le formulaire
- Cliquer sur "Payer avec Orange Money ML"

**4. Dans les logs, chercher:**
```
ORANGE_WEBPAY_RESPONSE | WebPayment Init | 
status=201 | 
body={...}
```

**Copier la réponse complète ici.**

---

## 💡 Hypothèses

### Hypothèse 1: URL Partagée (Plus Probable)

Orange Money utilise peut-être **la même URL sandbox** pour tous les pays:
- `https://webpayment-ow-sb.orange-money.com/` (universel)

Dans ce cas, le "ow" ne signifie pas "Guinée uniquement" mais "Orange Wallet" ou "Orange West Africa".

### Hypothèse 2: URL dans la Réponse

L'API retourne peut-être `payment_url` dans sa réponse, et nous devons juste l'utiliser telle quelle.

### Hypothèse 3: Construire l'URL avec pay_token

L'API retourne `pay_token` mais pas `payment_url`, et nous devons construire l'URL nous-mêmes, mais avec la bonne URL de base.

---

## 🚀 Action Immédiate

**1. Redémarrer Django:**
```bash
python manage.py runserver
```

**2. Tester avec le script:**
```bash
python test_orange_money_sandbox.py
```

**3. Copier la sortie complète ici**, surtout la partie:
```
ORANGE_WEBPAY_RESPONSE | WebPayment Init | 
status=201 | 
body={...}
```

**4. Je pourrai alors vous donner la solution définitive!**

---

## 📚 Référence

### URLs Orange Money Connues

| Type | URL | Status |
|------|-----|--------|
| Sandbox (Guinée/Ouest) | `webpayment-ow-sb.orange-money.com` | ✅ Existe |
| Sandbox (Mali) | `webpayment-ml-sb.orange-money.com` | ❌ N'existe pas |
| API Dev (Universal) | `api.orange.com/orange-money-webpay/dev/v1/webpayment` | ✅ Existe |

**Conclusion:** L'API `/dev/v1/webpayment` est universelle et retourne probablement l'URL correcte pour tous les pays.

---

## ✅ Prochaine Étape

**Lancez le test et copiez la réponse complète de l'API:**

```bash
cd auditshield
python test_orange_money_sandbox.py
```

Envoyez-moi la sortie, surtout la partie avec `ORANGE_WEBPAY_RESPONSE` et je vous donnerai la solution exacte! 🎯

