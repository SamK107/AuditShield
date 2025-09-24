# Recette CinetPay — Sandbox → Prod

## 1) Pré-requis
- Variables d’env en sandbox (local/staging), **aucun secret en code**.
- URLs BO CinetPay (sandbox) pointant vers:
  - Return: https://<ton-ngrok>.ngrok.io/payment/return/
  - Notify: https://<ton-ngrok>.ngrok.io/payment/callback/

## 2) Tests E2E (sandbox)
1. Lancer Django (`runserver`) + ngrok, configurer URLs dans le BO.
2. /offres/ → “Acheter” → CinetPay sandbox → retour.
3. Vérifier que **/payment/callback/** est bien reçu et qu’on fait **payment/check** avant de livrer.
4. Contrôler **idempotence**: 2e webhook ne relivre pas.

### Simulateur (local)
- Définir `CINETPAY_WEBHOOK_SECRET`.
- Exemples:
  - `python manage.py cinetpay_simulate_webhook --order ORD-1 --status PAID --signature ok`
  - `python manage.py cinetpay_simulate_webhook --order ORD-1 --status PAID --signature ok --repeat 2 --delay 2`
  - `python manage.py cinetpay_simulate_webhook --order ORD-2 --status PAID --signature bad` (→ 400 attendu)

## 3) Check-list Go-Live
- [ ] E2E sandbox validé (retour + webhook + `payment/check` + livraison UNIQUE).
- [ ] Signature webhook vérifiée (`x-token` par défaut) et **idempotence OK**.
- [ ] Montant/devise côté serveur (jamais depuis le navigateur).
- [ ] Logs clairs (order_id, statut, provider_tx_id).
- [ ] BO CinetPay **production**: Return/Notify → HTTPS vers auditsanspeur.com.
- [ ] Hébergeur: `CINETPAY_ENV=production`, `CINETPAY_API_KEY`, `CINETPAY_SITE_ID`, `CINETPAY_RETURN_URL`, `CINETPAY_NOTIFY_URL`.
- [ ] **Petit paiement réel** validé (500–1000 FCFA), livraison 1x.

## 4) Dépannage rapide
- 400 au webhook → vérifier signature/secret/header (`CINETPAY_WEBHOOK_HEADER`).
- Pas de livraison → confirmer `payment_check=OK` + transition `PENDING→PAID` avant `deliver_ebook`.
- Double livraison → verrou `select_for_update` + test `status != PAID` avant livraison.
- Pas de callback reçu en prod → HTTPS/pare-feu/URL Notify mal configurée dans le BO.
