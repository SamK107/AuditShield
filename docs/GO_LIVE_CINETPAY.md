# Go/No-Go CinetPay – Checklist de mise en production

## 1. Signature Webhook vérifiée
- [ ] Signature HMAC-SHA256 vérifiée sur `request.body` (pas sur le JSON reconstitué)
- [ ] Header configurable (`CINETPAY_WEBHOOK_HEADER`, défaut `x-token`)
- [ ] Secret via env (`CINETPAY_WEBHOOK_SECRET`), jamais en dur
- [ ] 3 formats acceptés : hex, sha256=<hex>, base64

## 2. Webhook callback sécurisé
- [ ] Signature vérifiée avant tout traitement
- [ ] Idempotence (pas de double livraison, verrou `select_for_update`)
- [ ] Appel serveur-à-serveur `payment_check` avant livraison
- [ ] 200 même sur 2e appel ou paiement déjà livré
- [ ] Logs sobres (jamais de secret)

## 3. Montant/devise côté serveur
- [ ] Montant et devise fixés côté serveur (DB), jamais depuis le navigateur
- [ ] Payload CinetPay construit uniquement avec valeurs serveur

## 4. Modèle Payment (unicité & statut)
- [ ] `order_id` unique
- [ ] `provider_tx_id` unique (si utilisé)
- [ ] Statut dans {INIT, PENDING, PAID, FAILED, CANCELED}
- [ ] Champ `updated_at` présent

## 5. Durcissement PROD (settings)
- [ ] `DJANGO_DEBUG=0` en prod
- [ ] `ALLOWED_HOSTS` correct (via env)
- [ ] Cookies sécurisés (`CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE`)
- [ ] `SECURE_PROXY_SSL_HEADER` si reverse proxy
- [ ] `CSRF_TRUSTED_ORIGINS` pour domaines prod
- [ ] HTTPS obligatoire pour Return/Notify

## 6. Tests Go/No-Go
- [ ] Tests unitaires couvrant : return non-livrant, signature 400/200, check KO/OK, idempotence
- [ ] Mocks sur `payment_check` et `deliver_ebook`

---

## Exemples d'export env (jamais de secrets en VCS)

```sh
export DJANGO_DEBUG=0
export ALLOWED_HOSTS="auditsanspeur.com,www.auditsanspeur.com"
export CINETPAY_WEBHOOK_HEADER=x-token
# export CINETPAY_WEBHOOK_SECRET=... (jamais en VCS)
```

## Rappels
- Les URLs Return/Notify doivent être en HTTPS.
- Toujours tester avec un **petit paiement réel** avant ouverture au public.
- Ne jamais livrer sur la page de retour (`/payment/return/`).
