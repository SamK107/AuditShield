# 🧪 Simuler un Paiement Orange Money Réussi

## 🎯 Objectif

Tester les pages de retour Orange Money **sans consommer de crédit sandbox**.

---

## 🚀 Méthode Rapide

### 1. Créer une commande de test

```bash
cd auditshield
python test_orange_success_page.py
```

**Ce script va** :
- ✅ Créer une commande factice avec status "PAID"
- ✅ Créer un token de téléchargement
- ✅ Vous donner toutes les URLs de test

### 2. Vous obtiendrez quelque chose comme :

```
🎯 URLS DE TEST
═══════════════════════════════════════════════════════════════════

✅ PAGE DE SUCCÈS (Return URL):
   http://127.0.0.1:8000/payments/om/return/?order_id=ORDER-abc123...

📥 PAGE DE TÉLÉCHARGEMENT:
   http://127.0.0.1:8000/downloads/secure/a1b2c3d4-e5f6-...

🎁 PAGE RESSOURCES BONUS:
   http://127.0.0.1:8000/downloads/resources/a1b2c3d4-e5f6-...

⚠️  PAGE D'ANNULATION (pour tester):
   http://127.0.0.1:8000/payments/om/cancel/?order_id=ORDER-abc123...
```

### 3. Copiez-collez l'URL de succès dans votre navigateur

---

## 🎬 Alternative : URL Directe Sans Script

Si vous ne voulez pas exécuter le script, voici comment obtenir une URL manuellement :

### Étape 1 : Créer une commande via Django Shell

```bash
python manage.py shell
```

```python
from store.models import Order, Product, DownloadToken
from django.utils import timezone
from datetime import timedelta

# Récupérer le produit
product = Product.objects.filter(is_published=True).first()

# Créer la commande
order = Order.objects.create(
    product=product,
    email="test@auditsanspeur.com",
    first_name="Test",
    last_name="Orange",
    phone="+22370123456",
    amount_fcfa=15000,
    currency="XOF",
    status="PAID",
    paid_at=timezone.now(),
)

# Créer le token
token = DownloadToken.objects.create(
    order=order,
    token=f"TEST-{order.uuid.hex[:16]}",
    expires_at=timezone.now() + timedelta(days=30),
    max_uses=999,
)

# Afficher les infos
print(f"UUID: {order.uuid}")
print(f"Provider ref: {order.provider_ref}")
print(f"\nURL Success:")
print(f"http://127.0.0.1:8000/payments/om/return/?order_id={order.provider_ref}")
```

### Étape 2 : Copiez l'URL affichée

---

## ✅ Ce que vous allez pouvoir tester

### 1. Page de Succès (`orange_success.html`)
- ✓ Design professionnel avec bannière verte
- ✓ Récapitulatif de la commande
- ✓ 3 boutons principaux :
  - Accéder à la page de téléchargement
  - Voir les ressources bonus
  - M'envoyer à nouveau les liens

### 2. Page de Téléchargement (`/downloads/secure/`)
- ✓ Accès aux 2 formats d'ebook (A4 + 6×9)
- ✓ Interface sécurisée

### 3. Page Ressources (`/downloads/resources/`)
- ✓ Accès aux bonus groupés par catégorie

### 4. Page d'Annulation (`orange_cancel.html`)
- ✓ Message d'annulation
- ✓ Bouton "Réessayer le paiement"

---

## 🧹 Nettoyage après les tests

Pour supprimer la commande de test :

```bash
python manage.py shell
```

```python
from store.models import Order
Order.objects.filter(email="test@auditsanspeur.com").delete()
```

---

## 💡 Avantages de cette Méthode

✅ **Gratuit** - Ne consomme pas votre crédit sandbox  
✅ **Rapide** - Test en 30 secondes  
✅ **Complet** - Teste tous les scénarios  
✅ **Réutilisable** - Peut être relancé autant de fois que nécessaire  
✅ **Réaliste** - Simule exactement ce que l'utilisateur verra  

---

## 🎬 Après ces tests

Une fois que vous avez validé que :
- ✓ La page de succès s'affiche correctement
- ✓ Les 3 boutons fonctionnent
- ✓ Le design est professionnel

Vous pouvez alors faire **un seul test réel** avec votre crédit sandbox pour vérifier l'intégration complète avec Orange Money WebPay.

---

## 🔄 Tester les Autres Scénarios

### Page en Attente (Pending)

Modifiez le status de la commande :

```python
order.status = "PENDING"
order.save()
```

Puis accédez à l'URL de retour → Vous verrez `orange_pending.html`

### Page d'Erreur (Unknown)

Accédez à l'URL sans paramètre :
```
http://127.0.0.1:8000/payments/om/return/
```

Vous verrez `orange_unknown.html`

---

## 🎉 Résultat

Vous pouvez maintenant tester toutes les pages sans consommer de crédit sandbox, puis faire **un seul test réel** pour valider l'intégration complète ! 🚀

