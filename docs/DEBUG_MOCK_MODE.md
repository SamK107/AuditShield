# Débogage - Mode MOCK activé par erreur

## 🔴 Problème

Quand vous cliquez sur "Payer avec CinetPay", vous êtes directement redirigé vers la page de remerciement au lieu de la page de paiement CinetPay.

## 🔍 Cause

Le mode MOCK est activé, ce qui simule le paiement au lieu d'appeler l'API réelle.

Quand le mode MOCK est activé :
1. `init_payment_auto` retourne une URL mock : `/payments/cinetpay/mock/`
2. Cette vue redirige automatiquement vers `cinetpay_return`
3. `payment_check` retourne toujours `True` en mode mock (si `DEBUG=True`)
4. La commande est marquée comme payée → page de remerciement

## ✅ Solution

### 1. Vérifier votre fichier `.env`

Assurez-vous que `CINETPAY_MOCK` n'est **PAS défini** ou est à `"0"` :

```env
# ❌ NE PAS FAIRE (active le mock)
CINETPAY_MOCK=1

# ✅ CORRECT (désactive le mock)
# Ne pas définir CINETPAY_MOCK du tout

# ✅ OU (explicite)
CINETPAY_MOCK=0
```

### 2. Vérifier les settings Django

Dans `config/settings/base.py`, ligne 189 :
```python
CINETPAY_MOCK = os.getenv("CINETPAY_MOCK", "0") == "1"
```

Cette ligne vérifie si `CINETPAY_MOCK=1` dans l'environnement.

### 3. Vérifier les logs

Quand vous testez un paiement, vérifiez les logs pour voir :

**Si le mode MOCK est activé, vous verrez :**
```
[CinetPay] Mode MOCK activé via CINETPAY_MOCK=1 dans .env
[CINETPAY MOCK MODE] init_payment_auto -> order_id=XXX tx=XXX
[KIT_CHECKOUT] ⚠️ ATTENTION: Redirection vers MOCK au lieu de l'API réelle!
```

**Si l'API réelle est utilisée, vous verrez :**
```
[CinetPay] Mode MOCK désactivé - Utilisation de l'API réelle
[CinetPay] Mode PRODUCTION - Appel API réelle pour order_id=XXX
[CinetPay][_post] Calling API: https://api-checkout.cinetpay.com/v2/payment
[KIT_CHECKOUT] ✅ Redirection vers API CinetPay réelle: https://secure.cinetpay.com/...
```

## 🔧 Vérification rapide

1. Ouvrez votre fichier `.env`
2. Cherchez la ligne `CINETPAY_MOCK`
3. Si elle existe et vaut `1`, changez-la en `0` ou supprimez-la
4. Redémarrez votre serveur Django
5. Testez à nouveau le paiement

## 📝 Variables requises pour l'API réelle

Votre `.env` doit contenir :
```env
CINETPAY_API_URL=https://api-checkout.cinetpay.com
CINETPAY_API_KEY=votre_cle_api_reelle
CINETPAY_SITE_ID=votre_site_id_reel
# CINETPAY_MOCK non défini ou = "0"
```

## 🚨 Diagnostic

Si le problème persiste, ajoutez ces logs temporaires dans `store/services/cinetpay.py` :

```python
def _is_mock_enabled() -> bool:
    env_value = os.getenv("CINETPAY_MOCK", "non défini")
    print(f"DEBUG: CINETPAY_MOCK = {env_value}")
    # ... reste du code
```

Cela vous permettra de voir exactement quelle valeur est lue depuis l'environnement.

