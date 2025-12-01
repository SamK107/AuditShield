# Solution : Redirection vers page de remerciement au lieu du checkout CinetPay

## Diagnostic effectué

Le script de diagnostic a vérifié votre configuration `.env` et a trouvé :
- ✅ `CINETPAY_MOCK` : NON DÉFINI (mode mock désactivé)
- ✅ `CINETPAY_API_KEY` : Présente
- ✅ `CINETPAY_SITE_ID` : Présent
- ✅ `CINETPAY_API_URL` : https://api-checkout.cinetpay.com
- ✅ `CINETPAY_RETURN_URL` : http://127.0.0.1:8000/payments/cinetpay/return/
- ✅ `CINETPAY_NOTIFY_URL` : http://127.0.0.1:8000/payments/cinetpay/notify/
- ✅ `CINETPAY_ENV` : sandbox

**La configuration semble correcte**, mais vous êtes toujours redirigé vers la page de remerciement.

## Causes possibles

### 1. Erreur lors de l'appel API CinetPay

Si l'appel à l'API CinetPay échoue (clés invalides, erreur réseau, etc.), le système pourrait :
- Lever une exception qui est capturée
- Rediriger vers une page d'erreur ou de fallback

**Vérification :**
1. Regardez les logs Django dans votre console quand vous cliquez sur "Payer avec CinetPay"
2. Cherchez les messages commençant par `[CinetPay]` ou `[KIT_CHECKOUT]`
3. Vérifiez s'il y a des erreurs comme :
   - `CINETPAY_INIT status=400` ou `status=401`
   - `Erreur réseau vers CinetPay`
   - `Configuration CinetPay incomplète`

### 2. Clés API invalides ou en mode sandbox

Si vos clés API sont invalides ou ne correspondent pas au mode (`sandbox` vs `production`), l'API CinetPay peut retourner une erreur.

**Vérification :**
- Assurez-vous que vos clés `CINETPAY_API_KEY` et `CINETPAY_SITE_ID` sont valides
- Si vous êtes en mode `sandbox`, utilisez les clés de test CinetPay
- Si vous êtes en mode `production`, utilisez les clés de production

### 3. URL de retour qui redirige immédiatement

Il est possible que l'URL retournée par CinetPay soit incorrecte ou que le flux soit interrompu.

**Vérification :**
- Dans les logs, cherchez : `[KIT_CHECKOUT] Redirecting to CinetPay:`
- Vérifiez que l'URL commence par `https://secure.cinetpay.com` ou `https://api-checkout.cinetpay.com`
- Si l'URL commence par `/payments/cinetpay/mock/`, c'est que le mode mock est activé quelque part

### 4. Mode mock activé dans settings.py

Le mode mock peut être activé dans `config/settings/base.py` ou `config/settings/dev.py` même si ce n'est pas dans `.env`.

**Vérification :**
```python
# Dans config/settings/base.py ligne 189
CINETPAY_MOCK = os.getenv("CINETPAY_MOCK", "0") == "1"
```

Si cette ligne est modifiée ou si `CINETPAY_MOCK` est défini ailleurs, cela pourrait activer le mode mock.

## Solutions à essayer

### Solution 1 : Vérifier les logs Django

1. Redémarrez votre serveur Django
2. Cliquez sur "Payer avec CinetPay"
3. Regardez immédiatement la console pour voir les messages de log
4. Cherchez les messages suivants :
   - `[CinetPay][init_payment_auto] Mode MOCK: True` → Mode mock activé
   - `[CinetPay][init_payment_auto] Mode MOCK: False` → Mode production
   - `[CINETPAY MOCK MODE]` → Mode mock activé
   - `[KIT_CHECKOUT] Redirecting to CinetPay:` → URL de redirection
   - `[CinetPay][_post] Calling API:` → Appel API réel
   - `CINETPAY_INIT status=` → Statut de la réponse API

### Solution 2 : Forcer explicitement le mode production

Ajoutez dans votre `.env` :
```env
CINETPAY_MOCK=0
```

Même si ce n'est pas défini, le forcer explicitement à `0` garantit qu'il n'est pas activé.

### Solution 3 : Vérifier que les clés API sont valides

Testez vos clés API avec curl ou Postman :

```bash
curl -X POST https://api-checkout.cinetpay.com/v2/payment \
  -H "Content-Type: application/json" \
  -d '{
    "apikey": "VOTRE_API_KEY",
    "site_id": "VOTRE_SITE_ID",
    "transaction_id": "TEST123",
    "amount": 1000,
    "currency": "XOF",
    "description": "Test"
  }'
```

Si vous obtenez une erreur `401` ou `403`, vos clés sont invalides.

### Solution 4 : Ajouter des logs de debug

Modifiez temporairement `store/views.py` ligne 461 pour ajouter plus de logs :

```python
redirect_url = cinetpay.init_payment_auto(
    order=order,
    request=request,
)
logger.info(f"[DEBUG] URL retournee: {redirect_url}")
logger.info(f"[DEBUG] Est-ce une URL mock? {redirect_url.startswith('/payments/cinetpay/mock/')}")
logger.info(f"[DEBUG] Est-ce une URL CinetPay? {'cinetpay.com' in redirect_url or 'secure.cinetpay' in redirect_url}")
```

### Solution 5 : Vérifier le code de `init_payment_auto`

Le code dans `store/services/cinetpay.py` ligne 523 vérifie le mode mock. Vérifiez que cette fonction retourne bien une URL CinetPay réelle et non une URL mock.

## Test rapide

Pour tester rapidement si le problème vient du mode mock ou de l'API :

1. **Test 1 : Forcer le mode mock**
   - Ajoutez `CINETPAY_MOCK=1` dans `.env`
   - Redémarrez Django
   - Cliquez sur "Payer avec CinetPay"
   - Si vous voyez la page de remerciement → Le mode mock fonctionne (c'est normal)
   - Remettez `CINETPAY_MOCK=0`

2. **Test 2 : Vérifier l'appel API**
   - Regardez les logs quand vous cliquez sur "Payer avec CinetPay"
   - Si vous voyez `[CinetPay][_post] Calling API: https://api-checkout.cinetpay.com/v2/payment` → L'API est appelée
   - Si vous voyez `CINETPAY_INIT status=201` → L'API a répondu avec succès
   - Si vous voyez `CINETPAY_INIT status=400` ou `401` → Erreur API (clés invalides)

## Action immédiate recommandée

1. **Ouvrez votre console Django** (où tourne `python manage.py runserver`)
2. **Cliquez sur "Payer avec CinetPay"** sur `http://127.0.0.1:8000/kit/inquiry/34/checkout/`
3. **Regardez immédiatement les logs** dans la console
4. **Copiez tous les messages** qui contiennent `[CinetPay]` ou `[KIT_CHECKOUT]`
5. **Partagez ces logs** pour qu'on puisse identifier le problème exact

Les logs vous diront exactement :
- Si le mode mock est activé ou non
- Si l'API CinetPay est appelée
- Quelle URL est retournée
- S'il y a des erreurs

## Fichiers à vérifier

1. `auditshield/.env` - Variables d'environnement
2. `auditshield/config/settings/base.py` ligne 189 - Configuration CINETPAY_MOCK
3. `auditshield/config/settings/dev.py` - Surcharges de développement
4. `auditshield/store/services/cinetpay.py` ligne 469-486 - Fonction `_is_mock_enabled()`
5. `auditshield/store/views.py` ligne 461 - Appel `init_payment_auto()`

