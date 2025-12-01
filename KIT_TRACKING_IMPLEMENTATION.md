# Implémentation du système de suivi Kit personnalisé

## ✅ Fichiers créés/modifiés

### Nouveaux fichiers
- `store/models.py` - Ajout du modèle `KitOrder`
- `store/services/kit_orders.py` - Service pour créer et gérer les KitOrder
- `store/kit_views.py` - Vues pour payment success, tracking, starter pack
- `store/templates/store/kit_payment_success.html` - Page de confirmation après paiement
- `store/templates/store/kit_tracking.html` - Page de suivi avec étapes
- `store/templates/emails/kit_order_received.html` - Template email HTML
- `store/templates/emails/kit_order_received.txt` - Template email texte

### Fichiers modifiés
- `store/urls.py` - Ajout des routes pour kit tracking
- `store/payment_views.py` - Intégration création KitOrder après paiement OM
- `store/views.py` - Intégration création KitOrder après paiement CinetPay
- `store/tasks.py` - Ajout tâche Celery `send_kit_progress_update`
- `store/admin.py` - Enregistrement KitOrder dans l'admin

## 📋 Commandes à exécuter

### 1. Migrations
```bash
# Créer la migration pour le nouveau modèle KitOrder
python manage.py makemigrations store

# Appliquer la migration
python manage.py migrate store
```

### 2. Créer le fichier Starter Pack
```bash
# Créer le répertoire assets à la racine du projet si nécessaire
mkdir -p assets

# Placer votre fichier PDF starter_pack.pdf dans ce répertoire
# Le chemin attendu est: auditshield/assets/starter_pack.pdf
# OU dans STATIC_ROOT/starter_pack.pdf
# OU dans MEDIA_ROOT/starter_pack.pdf
```

### 3. Configuration Celery (optionnel)
Si vous souhaitez utiliser la tâche de progression automatique, ajoutez dans votre configuration Celery Beat :

```python
# config/celery.py ou config/settings/base.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-kit-progress-updates': {
        'task': 'store.tasks.send_kit_progress_update',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h
        # Note: Cette tâche nécessite de passer le kit_order_id
        # Vous devrez peut-être créer une tâche wrapper qui trouve
        # tous les KitOrder en statut ANALYSIS et les traite
    },
}
```

**Alternative manuelle** : Vous pouvez appeler la tâche manuellement depuis l'admin Django ou via le shell :

```python
from store.tasks import send_kit_progress_update
from store.models import KitOrder

# Pour un KitOrder spécifique
kit_order = KitOrder.objects.get(tracking_id="KCP-00001")
send_kit_progress_update.delay(kit_order.id)
```

### 4. Collectstatic (si nécessaire)
```bash
python manage.py collectstatic --noinput
```

## 🔄 Flux de fonctionnement

1. **Client remplit le formulaire** `/kit/inquiry/`
2. **Client est redirigé vers** `/kit/inquiry/<id>/devis/`
3. **Client choisit le mode de paiement** (CinetPay ou Orange Money)
4. **Après paiement réussi** :
   - Un `KitOrder` est créé automatiquement
   - Un email de confirmation est envoyé
   - Le client est redirigé vers `/kit/payment/success/<tracking_id>/`
5. **Le client peut** :
   - Télécharger le Starter Pack immédiatement
   - Consulter la page de suivi `/kit/track/<tracking_id>/`

## 🎯 Points d'intégration

### CinetPay
- `store/views.py::cinetpay_return()` - Crée KitOrder et redirige
- `store/views.py::cinetpay_notify()` - Crée KitOrder (webhook)

### Orange Money
- `store/payment_views.py::om_return()` - Crée KitOrder et redirige
- `store/payment_views.py::om_notify()` - Crée KitOrder (webhook)
- `store/payment_views.py::om_mock_confirm()` - Crée KitOrder (mode mock)

## 📧 Emails

Les emails sont envoyés automatiquement via `store/services/kit_orders.py::send_kit_order_confirmation_email()`.

Ils contiennent :
- Numéro de suivi
- Détails de la commande
- Lien vers le Starter Pack
- Lien vers la page de suivi

## 🔍 Admin Django

Le modèle `KitOrder` est enregistré dans l'admin avec :
- Liste : tracking_id, full_name, email, offer, status, amount, created_at, delivery_date
- Filtres : status, offer, created_at, delivery_date
- Recherche : tracking_id, email, full_name
- Édition : status et delivery_date modifiables

## ⚠️ Notes importantes

1. **Starter Pack PDF** : Assurez-vous que le fichier `starter_pack.pdf` existe dans l'un des chemins suivants :
   - `BASE_DIR/assets/starter_pack.pdf`
   - `STATIC_ROOT/starter_pack.pdf`
   - `MEDIA_ROOT/starter_pack.pdf`

2. **Tracking ID** : Généré automatiquement au format `KCP-00001`, `KCP-00002`, etc.

3. **Délais** : Les délais sont calculés automatiquement selon l'offre :
   - Essentiel+ : 72h (3 jours)
   - Complet Pro : 96h (4-5 jours)
   - Expert Audit : 120h (5-7 jours)

4. **Statuts** : Les statuts peuvent être mis à jour manuellement depuis l'admin ou via la tâche Celery.

## 🧪 Tests

Pour tester le système :

1. **Mode mock** : Utilisez le mode mock Orange Money (`OM_SANDBOX_MOCK=1`)
2. **Créer une commande test** :
   ```python
   from store.models import KitOrder, ClientInquiry, Order
   from store.services.kit_orders import create_kit_order_from_payment
   
   # Créer un Order et ClientInquiry de test, puis :
   kit_order = create_kit_order_from_payment(order, inquiry)
   ```

3. **Vérifier les URLs** :
   - `/kit/payment/success/KCP-00001/`
   - `/kit/track/KCP-00001/`
   - `/kit/starter-pack/`

