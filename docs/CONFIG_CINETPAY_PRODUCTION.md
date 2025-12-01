# Configuration CinetPay - Utilisation API Réelle en Production

## ✅ Confirmation : Votre configuration permet l'utilisation de l'API CinetPay réelle

Votre configuration actuelle est **correcte** pour utiliser l'API CinetPay réelle en production, même en mode développement.

---

## 📋 Configuration actuelle

### 1. Chargement des variables d'environnement

**Fichier : `config/settings/dev.py`**
- ✅ Le fichier `.env` est chargé automatiquement (lignes 104 et 114)
- ✅ Utilise `load_dotenv()` pour charger toutes les variables

### 2. Mode MOCK désactivé par défaut

**Fichier : `store/services/cinetpay.py` (ligne 427)**
```python
def _is_mock_enabled() -> bool:
    return os.getenv("CINETPAY_MOCK", "0") == "1"
```
- ✅ Par défaut, le mode MOCK est **DÉSACTIVÉ** (`"0"`)
- ✅ Pour utiliser l'API réelle : **ne pas définir** `CINETPAY_MOCK` ou le mettre à `"0"`
- ⚠️ Le mode MOCK ne s'active que si vous définissez explicitement `CINETPAY_MOCK=1`

### 3. Utilisation de l'API réelle

**Fichier : `store/services/cinetpay.py` (lignes 16-31)**
```python
API_URL = os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com")
API_KEY = os.getenv("CINETPAY_API_KEY")
SITE_ID = os.getenv("CINETPAY_SITE_ID")
```

- ✅ Utilise l'URL de production par défaut : `https://api-checkout.cinetpay.com`
- ✅ Lit les clés depuis les variables d'environnement (fichier `.env`)

### 4. Vérification des clés avant appel API

**Fichier : `store/services/cinetpay.py` (lignes 482-488)**
```python
# Vérifier que les clés API sont configurées
if not API_KEY or not SITE_ID:
    logger.error("[CinetPay] API_KEY ou SITE_ID manquants")
    raise CinetPayError("Configuration CinetPay incomplète...")
```

- ✅ Le code vérifie que les clés sont présentes avant d'appeler l'API
- ✅ Affiche un message d'erreur clair si les clés manquent

---

## 🔧 Variables requises dans votre fichier `.env`

Assurez-vous que votre fichier `.env` contient les variables suivantes :

```env
# ============================================
# Configuration CinetPay - API Production
# ============================================

# URL de l'API CinetPay (production)
CINETPAY_API_URL=https://api-checkout.cinetpay.com

# Clés API de production (obtenues depuis votre back-office CinetPay)
CINETPAY_API_KEY=votre_cle_api_production_ici
CINETPAY_SITE_ID=votre_site_id_production_ici

# URLs de retour (optionnel - sera généré automatiquement si non défini)
CINETPAY_RETURN_URL=http://127.0.0.1:8000/payments/cinetpay/return/
CINETPAY_NOTIFY_URL=http://127.0.0.1:8000/payments/cinetpay/notify/

# IMPORTANT : Mode MOCK désactivé (pour utiliser l'API réelle)
# Ne pas définir cette variable, ou la mettre à "0"
# CINETPAY_MOCK=0

# Optionnel : Mode environnement (sandbox/production)
# Note : CinetPay utilise les mêmes clés pour sandbox et production
CINETPAY_ENV=production
```

---

## 🔄 Flux de paiement avec API réelle

Quand l'utilisateur clique sur **"Payer avec CinetPay"** :

1. **Vérification du mode** (ligne 464)
   - Si `CINETPAY_MOCK` n'est pas défini ou = "0" → **Mode PRODUCTION**
   - Si `CINETPAY_MOCK=1` → Mode MOCK (simulation locale)

2. **Vérification des clés** (lignes 482-488)
   - Vérifie que `CINETPAY_API_KEY` et `CINETPAY_SITE_ID` sont présents
   - Si manquants : erreur avec message clair

3. **Appel API réelle** (ligne 491)
   - Appelle `_REAL_init_payment_auto()` qui :
     - Construit le payload avec vos clés réelles
     - Fait un POST vers `https://api-checkout.cinetpay.com/v2/payment`
     - Utilise `requests.post()` pour appeler l'API réelle
     - Retourne l'URL de paiement CinetPay

4. **Redirection utilisateur**
   - L'utilisateur est redirigé vers la page de paiement CinetPay réelle
   - Il paie avec les moyens de paiement configurés dans votre compte CinetPay

5. **Retour après paiement**
   - CinetPay redirige vers `CINETPAY_RETURN_URL`
   - Webhook envoyé vers `CINETPAY_NOTIFY_URL`
   - Vérification du paiement et mise à jour du statut

---

## ✅ Checklist pour confirmer que l'API réelle est utilisée

- [ ] Votre fichier `.env` contient `CINETPAY_API_KEY` et `CINETPAY_SITE_ID` avec les vraies clés
- [ ] `CINETPAY_MOCK` n'est **pas défini** ou est égal à `"0"` dans votre `.env`
- [ ] `CINETPAY_API_URL` pointe vers `https://api-checkout.cinetpay.com`
- [ ] Les logs affichent `[CinetPay] Mode PRODUCTION - Appel API réelle pour order_id=X`
- [ ] Les logs affichent `[CinetPay][_post] Calling API: https://api-checkout.cinetpay.com/v2/payment`
- [ ] L'utilisateur est redirigé vers une URL CinetPay réelle (pas `/payments/cinetpay/mock/`)

---

## 🔍 Vérification dans les logs

Quand vous testez un paiement, vous devriez voir dans les logs :

```
[CinetPay] Mode PRODUCTION - Appel API réelle pour order_id=XXX
[CinetPay][_post] Calling API: https://api-checkout.cinetpay.com/v2/payment
[CinetPay][_post] Payload (masked): {'apikey': 'VOTRE_CLE...', 'site_id': 'XXX', ...}
CINETPAY_INIT status=201 body={"code":"201","message":"...","data":{"payment_url":"https://secure.cinetpay.com/..."}}
```

**Si vous voyez :**
```
[CINETPAY MOCK MODE] init_payment_auto -> ...
```
→ Le mode MOCK est activé, désactivez-le en retirant `CINETPAY_MOCK=1` du `.env`

---

## 🚨 Erreurs possibles

### "Configuration CinetPay incomplète"
- **Cause** : `CINETPAY_API_KEY` ou `CINETPAY_SITE_ID` manquants dans `.env`
- **Solution** : Vérifiez que ces variables sont bien définies dans votre `.env`

### Redirection vers `/payments/cinetpay/mock/`
- **Cause** : `CINETPAY_MOCK=1` est défini dans `.env`
- **Solution** : Retirez cette ligne ou mettez-la à `CINETPAY_MOCK=0`

### "Erreur réseau vers CinetPay"
- **Cause** : Problème de connexion à l'API CinetPay
- **Solution** : Vérifiez votre connexion internet et que l'URL `https://api-checkout.cinetpay.com` est accessible

---

## 📝 Conclusion

**Votre configuration actuelle permet bien d'utiliser l'API CinetPay réelle en production.**

- ✅ Le fichier `.env` est chargé automatiquement
- ✅ Le mode MOCK est désactivé par défaut
- ✅ Les clés API sont lues depuis les variables d'environnement
- ✅ L'API réelle est appelée si les clés sont présentes et le MOCK désactivé

Il vous suffit de :
1. Mettre vos vraies clés dans le fichier `.env`
2. S'assurer que `CINETPAY_MOCK` n'est pas défini ou est à `"0"`
3. Tester un paiement et vérifier dans les logs que l'API réelle est appelée

