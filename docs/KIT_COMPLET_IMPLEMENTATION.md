# Implémentation Flux Kit Complet - Résumé

## ✅ Fichiers créés/modifiés

### Modèles (`store/models.py`)
- ✅ Ajout `payment_status` et `processing_state` à `ClientInquiry`
- ✅ Ajout `order` FK à `ClientInquiry`
- ✅ Création `PaymentIntent` (provider, amount, external_ref, status)
- ✅ Création `GeneratedDraft` (OneToOne avec ClientInquiry)
- ✅ Création `FinalAsset` (OneToOne avec ClientInquiry)
- ✅ Modification `DownloadToken` pour supporter inquiry (FK nullable)

### Migrations
- ✅ Migration `0015_add_kit_complet_models.py` créée

### Services
- ✅ `store/services/orange_money.py` créé (structure similaire à CinetPay)
  - ⚠️ **TODO**: Adapter les endpoints Orange Money selon la vraie API

### Vues (`store/views.py`)
- ✅ `kit_checkout` - Page récap + choix paiement
- ✅ `kit_pay_cinetpay_start` - Init paiement CinetPay
- ✅ `kit_pay_om_start` - Init paiement Orange Money
- ✅ `cinetpay_notify` - Webhook idempotent (modifié)
- ✅ `orange_money_notify` - Webhook idempotent (nouveau)
- ✅ `kit_staff_list` - Liste staff avec badges
- ✅ `kit_upload_final` - Upload document final
- ✅ `kit_publish` - Publication avec guards
- ✅ `kit_secure_download` - Téléchargement sécurisé avec token

### Tâches Celery (`store/tasks.py`)
- ✅ `build_kit_word` modifié :
  - Vérifie `payment_status == "PAID"` avant démarrage
  - Vérifie `processing_state` (PAID/IA_RUNNING)
  - Utilise `docxtpl` pour générer le DOCX
  - Crée `GeneratedDraft` au lieu de `ai_doc`
  - Retry exponentiel (max 900s)

### Utilitaires
- ✅ `store/utils/tokens.py` :
  - `issue_download_token` - Génère token signé TTL court
  - `validate_download_token` - Valide signature/TTL
  - `consume_token` - Consomme token (incrémente used_count)

### Templates
- ✅ `store/templates/store/kit_checkout.html` - Page checkout
- ✅ `store/templates/store/kit_staff_list.html` - Liste staff avec badges

### URLs (`store/urls.py`)
- ✅ Routes ajoutées pour checkout, paiements, webhooks, staff, download

### Commandes management
- ✅ `store/management/commands/reconcile_payments.py` - Réconciliation PENDING > 15 min

## ⚠️ TODO / Configuration requise

### 1. Variables d'environnement
```bash
# Orange Money (à configurer selon la vraie API)
OM_API_URL=https://api.orange.com/orange-money-webpay/ml/v1
OM_MERCHANT_KEY=your_key
OM_MERCHANT_ID=your_id
OM_WEBHOOK_SECRET=your_secret
OM_RETURN_URL=https://yourdomain.com/payments/om/return/
OM_NOTIFY_URL=https://yourdomain.com/payments/om/notify/

# CinetPay (déjà configuré normalement)
CINETPAY_API_KEY=...
CINETPAY_SITE_ID=...
CINETPAY_WEBHOOK_SECRET=...
```

### 2. Template DOCX
- Créer un template `PRIVATE_MEDIA_ROOT/templates/kit_complet_template.docx`
- Variables disponibles dans le template docxtpl :
  - `organization_name`, `contact_name`, `email`
  - `statut_juridique`, `location`, `sector`
  - `mission_text`, `context_text`
  - `budget_range`, `funding_sources`, `audits_types`
  - `audits_frequency`, `staff_size`, `org_chart_text`, `notes_text`
  - `generated_content` (contenu généré par OpenAI)
  - `documents_count`

### 3. Service Orange Money
- ⚠️ **Adapter** `store/services/orange_money.py` selon la vraie API Orange Money
- Endpoints à adapter :
  - `create_checkout` - Init paiement
  - `verify_webhook` - Vérification signature
  - `check_transaction_status` - Vérification statut

### 4. Prix Kit Complet
- Dans `kit_inquiry` (ligne ~197), récupérer le bon produit
- Actuellement : `Product.objects.filter(slug="audit-sans-peur").first()`
- À adapter selon votre configuration produit

### 5. Tests
- Tests à ajouter (pytest) :
  - Webhook idempotent (double POST → 200, état stable)
  - Refus download si non payé
  - Émission token TTL + consommation unique
  - Tâche Celery ignorée si paiement non PAID

## 🔄 Flux complet

1. **Client** soumet formulaire → `kit_inquiry` POST
   - Crée `ClientInquiry` (payment_status=CREATED, processing_state=INQUIRY_RECEIVED)
   - Crée `Order` placeholder
   - Crée `PaymentIntent` placeholder
   - **NE PAS** lancer l'IA

2. **Client** choisit paiement → `kit_checkout`
   - Affiche récap (email, montant)
   - 2 boutons : CinetPay / Orange Money

3. **Client** clique bouton → `kit_pay_*_start`
   - Crée/mise à jour `PaymentIntent` (status=PENDING)
   - Appelle provider API
   - Redirige vers URL paiement

4. **Provider** webhook → `*_notify`
   - Vérifie signature
   - Idempotence : si déjà PAID → 200 OK
   - Sinon : payment_status=PAID, processing_state=PAID
   - **Enqueue Celery** `build_kit_word`

5. **Celery** `build_kit_word`
   - Guard : vérifie payment_status == PAID
   - Appelle OpenAI
   - Génère DOCX avec docxtpl
   - Crée `GeneratedDraft`
   - processing_state = DRAFT_DONE

6. **Staff** upload final → `kit_upload_final`
   - Upload DOCX final
   - Crée `FinalAsset`
   - processing_state = FINAL_UPLOADED

7. **Staff** publie → `kit_publish`
   - Guards : payment_status == PAID && processing_state == FINAL_UPLOADED
   - Génère `DownloadToken` (TTL 45 min, max_uses=1)
   - Envoie email avec lien
   - processing_state = PUBLISHED

8. **Client** télécharge → `kit_secure_download`
   - Valide token (signature, TTL, uses)
   - Vérifie payment_status == PAID
   - Consomme token (incrémente used_count)
   - Sert fichier depuis storage privé

## 🔧 Réconciliation

```bash
# Réconcilier les paiements en attente (> 15 min)
python manage.py reconcile_payments

# Mode dry-run (afficher sans modifier)
python manage.py reconcile_payments --dry-run

# Changer l'âge minimum
python manage.py reconcile_payments --min-age 30
```

## 📝 Notes importantes

- **Idempotence** : Tous les webhooks sont idempotents (rejouables sans effets de bord)
- **Transactions** : Utilisation de `transaction.atomic()` et `select_for_update()` pour les transitions d'état
- **Logs** : Tous les logs incluent `inquiry_id`, `order_id`, `provider`, `provider_ref`
- **Sentry** : Prêt si Sentry est configuré (exceptions loggées)
- **Storage** : Fichiers servis depuis `PRIVATE_MEDIA_ROOT` (storage privé/presigned S3)

## ✅ Critères d'acceptation

- [x] IA démarre uniquement suite à webhook PAID
- [x] Choix paiement via deux boutons sur `/kit/checkout/<id>/`
- [x] Publication bloquée si non PAID ou pas d'upload final
- [x] Lien de téléchargement signé, TTL court (45 min), usage limité (1)
- [x] Webhooks rejouables sans effets de bord
- [x] Réconciliation OK (commande créée)

