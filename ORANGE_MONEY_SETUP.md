# Configuration Orange Money WebPay Dev - Guide de Setup

## 📋 Informations nécessaires

Pour configurer Orange Money, vous avez besoin des informations suivantes fournies par Orange :

1. **OM_MERCHANT_MSISDN** : Numéro de téléphone marchand
2. **OM_MERCHANT_CODE** : Code marchand / Agent code
3. **OM_LOGIN** : Login (format: `MerchantWP0xxxxx`)
4. **OM_PASSWORD** : Mot de passe du simulateur

## 🔧 Étapes de configuration

### 1. Créer ou modifier le fichier `.env`

Le fichier `.env` doit se trouver à la racine du projet (même niveau que `manage.py`).

Si le fichier n'existe pas, copiez `ENV_TEMPLATE.txt` vers `.env` :

```bash
# Windows PowerShell
Copy-Item ENV_TEMPLATE.txt .env

# Linux/Mac
cp ENV_TEMPLATE.txt .env
```

### 2. Ajouter vos clés Orange Money dans `.env`

Ouvrez le fichier `.env` et ajoutez/modifiez les lignes suivantes dans la section Orange Money :

```env
# --- ORANGE MONEY WEBPAY DEV (Mali, Sandbox) ---
# Configuration pour le paiement de l'ebook "Audit Sans Peur"
OM_ENV=sandbox
OM_BASE_URL=https://api.orange.com/orange-money-webpay/dev

# Credentials Orange Money (À REMPLIR avec vos clés réelles)
OM_MERCHANT_MSISDN=votre_msisdn_ici
OM_MERCHANT_CODE=votre_merchant_code_ici
OM_LOGIN=MerchantWP0xxxxx
OM_PASSWORD=votre_mot_de_passe_ici

# Numéro de test sandbox (pour les simulations)
OM_TEST_SUBSCRIBER_MSISDN=77011011234

# Paramètres de paiement
OM_CURRENCY=XOF
OM_COUNTRY=ML

# URLs de retour et callback
OM_CALLBACK_URL=http://127.0.0.1:8000/store/orange/callback/
OM_RETURN_SUCCESS_URL=http://127.0.0.1:8000/store/orange/success/
OM_RETURN_FAILURE_URL=http://127.0.0.1:8000/store/orange/failure/
```

### 3. Exemple de configuration complète

Voici un exemple de ce que devrait contenir votre `.env` :

```env
# ... autres configurations existantes ...

# --- ORANGE MONEY WEBPAY DEV (Mali, Sandbox) ---
OM_ENV=sandbox
OM_BASE_URL=https://api.orange.com/orange-money-webpay/dev

# Remplacez ces valeurs par celles fournies par Orange
OM_MERCHANT_MSISDN=77012345678
OM_MERCHANT_CODE=1234567890
OM_LOGIN=MerchantWP01234
OM_PASSWORD=mon_mot_de_passe_secret

OM_TEST_SUBSCRIBER_MSISDN=77011011234
OM_CURRENCY=XOF
OM_COUNTRY=ML

OM_CALLBACK_URL=http://127.0.0.1:8000/store/orange/callback/
OM_RETURN_SUCCESS_URL=http://127.0.0.1:8000/store/orange/success/
OM_RETURN_FAILURE_URL=http://127.0.0.1:8000/store/orange/failure/
```

## ✅ Vérification de la configuration

### 1. Vérifier que le fichier `.env` est chargé

La configuration est automatiquement chargée par Django via `config/settings/dev.py`.

### 2. Tester la configuration

Une fois vos clés ajoutées, vous pouvez tester le flux :

1. Accéder à : `http://127.0.0.1:8000/buy/orange/audit-sans-peur/`
2. Remplir le formulaire de checkout
3. Cliquer sur "Payer avec Orange Money Mali"
4. Être redirigé vers la page de mock checkout
5. Simuler un paiement réussi

### 3. Vérifier les logs

Si l'API Orange Money est appelée, vous verrez les logs dans la console Django. Si les credentials manquent, le système basculera automatiquement en mode mock.

## 📍 Emplacements de configuration

### Fichier `.env` (À la racine du projet)
```
auditshield/
├── manage.py
├── .env          ← ICI : Ajoutez vos clés Orange Money
├── ENV_TEMPLATE.txt
└── ...
```

### Configuration Django (`config/settings/dev.py`)
Les lignes 188-201 lisent automatiquement les variables d'environnement depuis `.env` :

```python
ORANGE_MONEY = OrangeMoneyConfig(
    env=os.getenv("OM_ENV", "sandbox"),
    base_url=os.getenv("OM_BASE_URL", "https://api.orange.com/orange-money-webpay/dev"),
    merchant_msisdn=os.getenv("OM_MERCHANT_MSISDN", ""),
    merchant_code=os.getenv("OM_MERCHANT_CODE", ""),
    login=os.getenv("OM_LOGIN", ""),           # ← Lit depuis .env
    password=os.getenv("OM_PASSWORD", ""),     # ← Lit depuis .env
    # ...
)
```

## 🔒 Sécurité

⚠️ **Important** :
- Ne commitez **JAMAIS** le fichier `.env` dans Git
- Le fichier `.env` est déjà dans `.gitignore`
- En production, utilisez les variables d'environnement du serveur plutôt que le fichier `.env`

## 📝 Résumé des variables à renseigner

| Variable | Description | Exemple |
|----------|-------------|---------|
| `OM_MERCHANT_MSISDN` | Numéro de téléphone marchand | `77012345678` |
| `OM_MERCHANT_CODE` | Code marchand / Agent code | `1234567890` |
| `OM_LOGIN` | Login fourni par Orange | `MerchantWP01234` |
| `OM_PASSWORD` | Mot de passe du simulateur | `votre_mot_de_passe` |

## 🆘 En cas de problème

Si le paiement ne fonctionne pas :

1. Vérifiez que toutes les variables sont bien définies dans `.env`
2. Vérifiez que les valeurs sont correctes (pas d'espaces avant/après)
3. Redémarrez le serveur Django après modification du `.env`
4. Consultez les logs Django pour voir les erreurs

## 📞 Support

Pour toute question sur les clés Orange Money, contactez le support Orange Money Mali.

