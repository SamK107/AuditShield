# Dev Notes — AuditShield

## .env requis (extraits)

- CINETPAY_API_URL=https://api-checkout.cinetpay.com
- CINETPAY_API_KEY=...
- CINETPAY_SITE_ID=...
- CINETPAY_RETURN_URL=http://127.0.0.1:8000/cinetpay/return/
- CINETPAY_NOTIFY_URL=http://127.0.0.1:8000/payments/cinetpay/notify/
- CINETPAY_WEBHOOK_SECRET=... (pour signature HMAC)
- SITE_BASE_URL=http://127.0.0.1:8000
- FULFILMENT_SENDER=noreply@auditsanspeur.com
- RECEIPTS_IMAP_HOST=imap.example.com
- RECEIPTS_IMAP_PORT=993
- RECEIPTS_IMAP_USER=receipts@example.com
- RECEIPTS_IMAP_PASSWORD=********
- RECEIPTS_IMAP_FOLDER=INBOX

## Commandes utiles

```bash
python manage.py migrate
python manage.py test
python manage.py fetch_receipts --dry-run
python manage.py process_bonus_queue --sample
```

## Admin

- Paiements / Intentions: via `store` (PaymentIntent) ou `Payment` si activé
- ExternalEntitlement: app `downloads`
- Kit complet (staff): `/kit-complet-traitement/` (alias: `/bonus-resultat-kit-preparation/`)

## Scénarios de test manuel

- Paiement CinetPay:
  1. Démarrer un paiement
  2. Simuler webhook signée vers `/payments/cinetpay/notify/`
  3. Vérifier: PaymentIntent=PAID, email fulfilment reçu, tâche IA en file
- Liens signés:
  - Page `/downloads/secure/` doit proposer A4 et 6×9 avec URLs temporaires
- IMAP:
  - Lancer `fetch_receipts --dry-run` puis sans `--dry-run` sur une boîte de test
  - Vérifier créations `ExternalEntitlement` et réception email fulfilment


