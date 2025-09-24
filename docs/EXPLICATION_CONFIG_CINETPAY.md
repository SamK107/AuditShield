# Configuration CinetPay — Situation Actuelle et Instructions

## 1. Où sont stockées les clés et identifiants ?

Les identifiants CinetPay (`API_KEY`, `SITE_ID`, etc.) sont stockés dans les **variables d’environnement**.

- Ils peuvent être définis :
  - dans l’interface cPanel (Setup Python App → Variables d’environnement),
  - ou dans un fichier `.env` (non committé, utilisé avec python-dotenv).

**Exemple de variables à définir :**

```env
# .env — Configuration CinetPay

# Django
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=0
ALLOWED_HOSTS=ton-domaine.com,www.ton-domaine.com

# CinetPay (remplace les valeurs par celles de ton compte business)
CINETPAY_API_URL=https://api-checkout.cinetpay.com
CINETPAY_API_KEY=VOTRE_VRAIE_API_KEY_ICI
CINETPAY_SITE_ID=VOTRE_VRAI_SITE_ID_ICI
CINETPAY_RETURN_URL=https://ton-domaine.com/payment/return/
CINETPAY_NOTIFY_URL=https://ton-domaine.com/payment/callback/
```

> **Ne jamais committer le `.env` !**

---

## 2. Où sont-elles utilisées dans le code ?

Dans le fichier `store/services/cinetpay.py` :
- Les variables d’environnement sont lues via `os.getenv`.
- Elles servent à initialiser les paiements et à sécuriser les échanges avec CinetPay.

**Extrait de code :**

```python
API_URL = os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com")
APIKEY  = os.getenv("CINETPAY_API_KEY")
SITE_ID = os.getenv("CINETPAY_SITE_ID")
RETURN_URL = os.getenv("CINETPAY_RETURN_URL")
NOTIFY_URL = os.getenv("CINETPAY_NOTIFY_URL")
```

Lors de la création d’une transaction, le code envoie `apikey` et `site_id` à l’API CinetPay.

---

## 3. Endpoints à configurer côté CinetPay

Dans le back-office CinetPay, il faut renseigner :
- **Return URL** : `https://ton-domaine.com/payment/return/`
- **Notification URL** (webhook) : `https://ton-domaine.com/payment/callback/`

---

## 4. Sécurité

- Les secrets ne doivent jamais être en clair dans le code.
- Le webhook (`/payment/callback/`) doit vérifier le HMAC (`x-token`) et valider la transaction via `/v2/payment/check` avant de livrer le produit.

---

## 5. À faire pour la mise en production

- Remplacer les valeurs de test dans `.env` ou cPanel par les vraies valeurs business :
  - `CINETPAY_API_KEY`
  - `CINETPAY_SITE_ID`
  - Adapter les URLs si besoin (nom de domaine réel, HTTPS obligatoire).

---

## 6. Résumé visuel à transmettre

| Variable                | Où la mettre ?         | À remplacer par…         |
|-------------------------|------------------------|--------------------------|
| CINETPAY_API_KEY        | .env ou cPanel         | Ta vraie clé API         |
| CINETPAY_SITE_ID        | .env ou cPanel         | Ton vrai site_id         |
| CINETPAY_RETURN_URL     | .env ou cPanel         | URL publique HTTPS       |
| CINETPAY_NOTIFY_URL     | .env ou cPanel         | URL publique HTTPS       |

---

**En résumé :**
La configuration actuelle est prête à recevoir les vraies valeurs business. Il suffit de remplacer les valeurs de test par les vraies dans les variables d’environnement, sans toucher au code.

---

**À donner à ton collègue tel quel !**
