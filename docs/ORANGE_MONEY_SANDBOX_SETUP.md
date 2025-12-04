# Configuration Orange Money Sandbox - Guide Complet

## 🎯 Objectif

Configurer Orange Money WebPay Dev (Sandbox) pour tester les paiements sans utiliser ngrok.

## ⚠️ Important

Orange Money **n'accepte PAS** les URLs avec `localhost` ou `127.0.0.1`. Vous devez utiliser une **URL publique valide**.

## 📋 Étape 1 : Obtenir une URL publique de test

Pour le mode sandbox, vous avez plusieurs options pour obtenir une URL publique gratuite :

### Option A : Utiliser un service d'hébergement gratuit (Recommandé)

1. **Webnode** (comme dans les exemples du guide Orange Money) :
   - Créez un compte gratuit sur https://www.webnode.fr/
   - Créez un site simple
   - Vous obtiendrez une URL comme : `http://mon-site.webnode.es`
   - Utilisez cette URL comme base

2. **Autres services gratuits** :
   - **Netlify** : https://www.netlify.com/ (URL: `https://votre-site.netlify.app`)
   - **Vercel** : https://vercel.com/ (URL: `https://votre-site.vercel.app`)
   - **GitHub Pages** : https://pages.github.com/ (URL: `https://votre-username.github.io`)
   - **000webhost** : https://www.000webhost.com/ (URL: `https://votre-site.000webhostapp.com`)

### Option B : Utiliser votre propre domaine (si disponible)

Si vous avez un domaine, vous pouvez utiliser :
- `https://votre-domaine.com`
- `https://test.votre-domaine.com`

## 📋 Étape 2 : Configurer votre `.env`

Ajoutez dans votre fichier `.env` :

```env
# URL publique de test pour Orange Money Sandbox
# Remplacez par votre URL publique réelle
OM_TEST_PUBLIC_URL=https://votre-site.netlify.app
```

**Exemples selon le service choisi :**
```env
# Webnode
OM_TEST_PUBLIC_URL=http://mon-site.webnode.es

# Netlify
OM_TEST_PUBLIC_URL=https://mon-site.netlify.app

# Vercel
OM_TEST_PUBLIC_URL=https://mon-site.vercel.app

# GitHub Pages
OM_TEST_PUBLIC_URL=https://mon-username.github.io
```

## 📋 Étape 3 : Configurer les credentials Orange Money

Selon le guide Orange Money (`guide_orange.md`), vous devez avoir :

1. **Merchant Key** : Obtenu depuis le portail Orange Developer
2. **Client ID** et **Client Secret** : Pour l'authentification OAuth
3. **Merchant Account Number** et **Merchant Code** : Fournis par email

Ajoutez dans votre `.env` :

```env
# Orange Money WebPay Dev (Sandbox)
OM_CLIENT_ID=votre_client_id
OM_CLIENT_SECRET=votre_client_secret
OM_MERCHANT_KEY=votre_merchant_key
OM_MERCHANT_MSISDN=7701900100
OM_MERCHANT_ID=votre_merchant_id
```

## 📋 Étape 4 : Tester

1. Redémarrez votre serveur Django
2. Allez sur `/buy/audit-sans-peur/?provider=orange_money_ml`
3. Sélectionnez "Orange Money Mali"
4. Remplissez le formulaire
5. Cliquez sur "Payer avec Orange Money Mali"

## 🔍 Vérification

Dans les logs Django, vous devriez voir :
```
[OM][create_payment] Using test public URL: return=https://votre-site.netlify.app/payments/om/return/, notify=https://votre-site.netlify.app/payments/om/notify/
```

Au lieu de l'erreur sur localhost.

## ⚠️ Notes importantes

1. **Les URLs de retour ne doivent pas pointer vers votre serveur local** : Orange Money ne pourra pas y accéder
2. **Pour les webhooks (notify_url)** : En mode sandbox, Orange Money enverra les notifications à l'URL configurée, mais si cette URL n'est pas accessible publiquement, vous ne recevrez pas les notifications
3. **Pour tester les webhooks en local** : Vous devrez quand même utiliser ngrok ou un service similaire pour recevoir les webhooks

## 🚀 Alternative : Utiliser ngrok uniquement pour les webhooks

Si vous voulez éviter d'utiliser ngrok pour les URLs de retour mais l'utiliser uniquement pour recevoir les webhooks :

1. Configurez `OM_TEST_PUBLIC_URL` avec une URL publique de test
2. Configurez `OM_NGROK_URL` avec votre URL ngrok
3. Le code utilisera l'URL publique pour `return_url` et ngrok pour `notify_url`

## 📚 Références

- Guide Orange Money : `guide_orange.md`
- Documentation Orange Developer : https://developer.orange.com/

