# Intégration CinetPay – AuditShield

## Schéma de flux (E2E)

1. **Création paiement** (POST `/buy/<product_slug>/<tier_id>/`)
   - Serveur crée un Payment (order_id unique, montant, email)
   - Appelle l’API CinetPay (init_payment)
   - Retourne l’URL de paiement à rediriger côté client
2. **Redirection utilisateur**
   - L’utilisateur paie sur la page CinetPay
3. **Return URL** (`/payment/return/`)
   - Affiche un écran “Retour reçu, en attente de confirmation…”
   - Ne livre rien ici
4. **Webhook CinetPay** (`/payment/callback/`)
   - POST signé (header x-token)
   - Vérifie la signature HMAC
   - Idempotence : verrouille la transaction, refuse si déjà PAID
   - Appelle payment_check (serveur à serveur)
   - Si OK : Payment.status=PAID, provider_tx_id, livraison (lien unique expirable, e-mail)
   - Journalise un PaymentEvent
5. **Livraison**
   - Génère un lien de téléchargement unique et expirable (itsdangerous)
   - Envoie un e-mail de confirmation avec le lien
   - Ajoute un PaymentEvent(kind="DELIVERED")

---

## Variables d’environnement requises

| Variable                    | Exemple (dev)                                 | Description                                 |
|-----------------------------|-----------------------------------------------|---------------------------------------------|
| CINETPAY_ENV                | sandbox                                      | "sandbox" ou "production"                  |
| CINETPAY_API_URL            | https://api-checkout.cinetpay.com             | URL API CinetPay                            |
| CINETPAY_API_KEY            | SANDBOX_API_KEY_TODO                         | Clé API (jamais en code !)                  |
| CINETPAY_SITE_ID            | SANDBOX_SITE_ID_TODO                         | Site ID (jamais en code !)                  |
| CINETPAY_RETURN_URL         | https://<NGROK>.ngrok.io/payment/return/      | URL de retour après paiement                |
| CINETPAY_NOTIFY_URL         | https://<NGROK>.ngrok.io/payment/callback/    | URL du webhook (callback)                   |
| CINETPAY_WEBHOOK_SECRET     | secret_webhook                               | Secret HMAC pour signature webhook          |

---

## Procédure ngrok (dev)

1. Lancer le serveur Django :
   ```
   python manage.py runserver 8000
   ```
2. Lancer ngrok :
   ```
   ngrok http http://127.0.0.1:8000
   ```
3. Copier l’URL ngrok générée (ex : `https://xxxx.ngrok.io`)
4. Mettre à jour `.env.dev` :
   - `CINETPAY_RETURN_URL=https://xxxx.ngrok.io/payment/return/`
   - `CINETPAY_NOTIFY_URL=https://xxxx.ngrok.io/payment/callback/`
5. Déclarer ces URLs dans le back-office CinetPay (sandbox)

---

## Checklist Go-Live

- [ ] Sandbox E2E vert en local + staging
- [ ] Logs webhook & idempotence vérifiés
- [ ] E-mails OK (staging)
- [ ] BO CinetPay production : RETURN_URL / NOTIFY_URL prod déclarées
- [ ] En prod : remplir .env.prod (clés réelles) dans l’hébergeur (cPanel env), pas de commit
- [ ] Paiement réel “petit montant” validé E2E
- [ ] Token de téléchargement expirable confirmé

---

**Sécurité :**
- Aucun secret/API key en code ou commit
- Webhook refuse sans signature ou signature invalide
- Idempotence stricte (pas de double livraison)

**Tests :**
- start_checkout crée un Payment et appelle init_payment (mock requests.post)
- webhook sans signature → 400
- webhook signature mauvaise → 400
- webhook signature OK + payment_check KO → FAILED (pas de livraison)
- webhook signature OK + payment_check OK → PAID + livraison appelée
- webhook appelé 2x → idempotent (pas de 2nde livraison)
