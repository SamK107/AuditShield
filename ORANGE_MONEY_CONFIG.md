# Configuration Orange Money - Problèmes identifiés

## 🔴 Problèmes identifiés

### 1. Variables d'environnement manquantes dans `.env`

Le fichier `.env` ne contient **aucune** variable Orange Money. Il faut ajouter :

```env
# Orange Money Web Payment (Mali)
OM_API_URL=https://api.orange.com/orange-money-webpay/ml/v1
OM_MERCHANT_KEY=votre_merchant_key
OM_MERCHANT_ID=votre_merchant_id
OM_CLIENT_ID=votre_client_id
OM_CLIENT_SECRET=votre_client_secret
OM_WEBHOOK_SECRET=votre_webhook_secret
OM_RETURN_URL=http://127.0.0.1:8000/payments/om/return/
OM_NOTIFY_URL=http://127.0.0.1:8000/payments/om/notify/
```

### 2. API Orange Money incorrecte

Selon la [documentation Orange Money](https://developer.orange.com/apis/om-webpay), l'API Orange Money nécessite :

- **Authentification OAuth 2.0** : Il faut d'abord obtenir un token d'accès avec `client_id` et `client_secret`
- **Endpoints différents** : L'API réelle n'utilise probablement pas `/webpay/init` mais des endpoints spécifiques

Le code actuel dans `orange_money.py` :
- ❌ N'utilise pas OAuth pour obtenir un token
- ❌ Utilise des endpoints génériques (`/webpay/init`, `/webpay/check`)
- ❌ Structure de payload probablement incorrecte

### 3. Documentation Orange Money

D'après la documentation :
- Le service est disponible au **Mali, Cameroun, Côte d'Ivoire, Sénégal, Madagascar, Botswana, etc.**
- Il faut être un **merchant Orange Money officiel** (inscription en magasin Orange)
- L'API nécessite une **authentification OAuth 2.0**
- Les utilisateurs doivent générer un **OTP (One Time Password)** via USSD Orange Money

### 4. Vérification de l'URL du bouton

Le template `kit_checkout.html` utilise :
```html
<form method="post" action="{% url 'store:kit_pay_om_start' inquiry.id %}">
```

L'URL dans `urls.py` est :
```python
path("payments/kit/om/start/<int:inquiry_id>/", views.kit_pay_om_start, name="kit_pay_om_start"),
```

✅ **L'URL est correcte** - le problème vient probablement de l'API Orange Money qui échoue silencieusement.

## ✅ Corrections nécessaires

### Étape 1 : Ajouter les variables dans `.env`

Ajoutez les variables Orange Money dans votre fichier `.env` à la racine du projet.

### Étape 2 : Obtenir les credentials Orange Money

1. Contactez Orange Mali pour devenir un merchant Orange Money
2. Inscrivez-vous au service Web Payment / M Payment
3. Obtenez vos credentials :
   - `OM_MERCHANT_KEY`
   - `OM_MERCHANT_ID`
   - `OM_CLIENT_ID` (pour OAuth)
   - `OM_CLIENT_SECRET` (pour OAuth)
   - `OM_WEBHOOK_SECRET`

### Étape 3 : Corriger l'implémentation de l'API

L'API Orange Money nécessite probablement :

1. **OAuth 2.0 Authentication** :
   ```python
   # Obtenir un token d'accès
   token_response = requests.post(
       "https://api.orange.com/oauth/v2/token",
       data={
           "grant_type": "client_credentials",
           "client_id": OM_CLIENT_ID,
           "client_secret": OM_CLIENT_SECRET
       }
   )
   access_token = token_response.json()["access_token"]
   ```

2. **Utiliser le token dans les requêtes** :
   ```python
   headers = {
       "Authorization": f"Bearer {access_token}",
       "Content-Type": "application/json"
   }
   ```

3. **Endpoints corrects** : Consultez la documentation Orange Money pour les vrais endpoints.

### Étape 4 : Vérifier les logs

Quand vous cliquez sur "Payer par Orange Money ML", vérifiez :
- Les logs Django pour voir l'erreur exacte
- La console du navigateur pour les erreurs JavaScript
- Les logs réseau pour voir si la requête est envoyée

## 🔍 Diagnostic immédiat

Pour diagnostiquer pourquoi le bouton ne fait rien :

1. **Vérifier les variables d'environnement** :
   ```python
   # Dans la vue kit_pay_om_start, ajouter :
   import os
   logger.info(f"OM_MERCHANT_KEY: {bool(os.getenv('OM_MERCHANT_KEY'))}")
   logger.info(f"OM_MERCHANT_ID: {bool(os.getenv('OM_MERCHANT_ID'))}")
   ```

2. **Vérifier si l'exception est capturée** :
   La vue `kit_pay_om_start` capture les exceptions mais peut-être que l'erreur se produit avant.

3. **Tester avec des credentials mock** :
   Pour le développement, vous pouvez temporairement retourner une URL mock si les credentials sont manquants.

## ✅ Corrections apportées

### 1. Amélioration du code Orange Money
- ✅ Ajout de la fonction `get_oauth_token()` pour l'authentification OAuth 2.0
- ✅ Support des variables `OM_CLIENT_ID` et `OM_CLIENT_SECRET`
- ✅ Meilleure gestion des erreurs avec messages explicites
- ✅ Logging amélioré pour le diagnostic

### 2. Amélioration de la vue
- ✅ Gestion spécifique des erreurs `OrangeMoneyError`
- ✅ Messages d'erreur plus clairs pour l'utilisateur
- ✅ Logging détaillé pour le débogage

### 3. Amélioration du template
- ✅ Affichage des messages d'erreur Django dans `kit_checkout.html`

## 📝 Actions immédiates à faire

1. ✅ **Ajouter les variables Orange Money dans `.env`** :
   ```env
   OM_MERCHANT_KEY=votre_merchant_key
   OM_MERCHANT_ID=votre_merchant_id
   OM_CLIENT_ID=votre_client_id
   OM_CLIENT_SECRET=votre_client_secret
   OM_WEBHOOK_SECRET=votre_webhook_secret
   ```

2. ✅ **Obtenir les credentials Orange Money** :
   - Contactez Orange Mali pour devenir merchant
   - Inscrivez-vous au service Web Payment
   - Obtenez vos credentials depuis le portail Orange Developer

3. ✅ **Tester après configuration** :
   - Cliquez sur "Payer par Orange Money ML"
   - Vérifiez les logs Django pour voir l'erreur exacte
   - Vérifiez que les messages d'erreur s'affichent sur la page

4. ⚠️ **Adapter les endpoints si nécessaire** :
   - Les endpoints actuels (`/webpay/init`, `/webpay/check`) sont des estimations
   - Consultez la documentation Orange Money pour les vrais endpoints
   - L'URL OAuth par défaut est `https://api.orange.com/oauth/v2/token` mais peut varier

## 🔗 Ressources

- [Orange Money Web Payment Documentation](https://developer.orange.com/apis/om-webpay)
- [Orange Developer Portal](https://developer.orange-sonatel.com/)

