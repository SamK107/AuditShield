# PAYMENT_CINETPAY.md

Intégration **CinetPay Checkout** dans un site Django hébergé sur **LWS cPanel (Passenger/WSGI)**.
Objectif : créer une transaction, rediriger l’utilisateur, recevoir le **webhook** sécurisé, **vérifier** la transaction côté API, puis délivrer le PDF via un **lien sécurisé**.

> Sur LWS cPanel, pas de serveur custom (pas de Gunicorn/Nginx) : l’app tourne en **WSGI** via Passenger derrière Apache. C’est compatible avec tout ce qui suit.

---

## 1) Variables d’environnement (cPanel)

Dans **cPanel → Setup Python App**, ajoute (ou via `.env` + python-dotenv) :

- `DJANGO_SETTINGS_MODULE` = `config.settings`
- `DJANGO_SECRET_KEY` = `…`
- `CINETPAY_API_URL` = `https://api-checkout.cinetpay.com`
- `CINETPAY_API_KEY` = `…`
- `CINETPAY_SITE_ID` = `…`
- `CINETPAY_RETURN_URL` = `https://ton-domaine/payment/return/`
- `CINETPAY_NOTIFY_URL` = `https://ton-domaine/payment/callback/`

Astuce : utilise bien **les URLs publiques en HTTPS** (pas `localhost`).

---

## 2) Initialiser un paiement (création d’URL)

Dans `store/services/cinetpay.py` :

    # store/services/cinetpay.py
    import os, requests

    API_URL = os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com")
    APIKEY  = os.getenv("CINETPAY_API_KEY")
    SITE_ID = os.getenv("CINETPAY_SITE_ID")
    RETURN_URL = os.getenv("CINETPAY_RETURN_URL")
    NOTIFY_URL = os.getenv("CINETPAY_NOTIFY_URL")

    class CinetPayError(Exception):
        pass

    def init_payment(*, transaction_id: str, amount: int, currency: str, description: str,
                     channels: str = "ALL", customer: dict | None = None) -> str:
        """
        Crée une transaction CinetPay et retourne l'URL de paiement.
        """
        payload = {
            "apikey": APIKEY,
            "site_id": SITE_ID,
            "transaction_id": transaction_id,  # unique
            "amount": amount,                   # XOF/XAF : multiple de 5
            "currency": currency,               # "XOF" en général
            "description": description,         # éviter chars spéciaux
            "notify_url": NOTIFY_URL,
            "return_url": RETURN_URL,
            "channels": channels,               # "ALL" ou "MOBILE_MONEY"/"CREDIT_CARD"/...
            "metadata": transaction_id,
        }
        if customer:
            payload.update({
                "customer_id": customer.get("id"),
                "customer_name": customer.get("name"),
                "customer_surname": customer.get("surname"),
                "customer_email": customer.get("email"),
                "customer_phone_number": customer.get("phone"),
                "customer_address": customer.get("address"),
                "customer_city": customer.get("city"),
                "customer_country": customer.get("country"),  # ISO2 ex: ML, CI, SN
                "customer_state": customer.get("state", ""),
                "customer_zip_code": customer.get("zip", "00000"),
            })

        r = requests.post(f"{API_URL}/v2/payment", json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != "201":
            raise CinetPayError(f"Init failed: {data}")
        return data["data"]["payment_url"]

---

## 3) Vue d’achat (création de l’Order + redirection CinetPay)

Dans `store/views.py` :

    # store/views.py (extrait)
    import uuid
    from django.shortcuts import get_object_or_404, render, redirect
    from .models import Product, Order, DownloadToken
    from .services.cinetpay import init_payment, CinetPayError

    def buy(request, slug):
        if request.method != "POST":
            return redirect("store:product_detail", slug=slug)

        product = get_object_or_404(Product, slug=slug, is_published=True)

        # 1) Créer l'Order en pending + transaction_id CinetPay
        tx_id = uuid.uuid4().hex[:24].upper()
        order = Order.objects.create(
            product=product,
            email=request.POST.get("email", "client@example.com"),
            amount_fcfa=product.price_fcfa,
            status=Order.PENDING,
            cinetpay_payment_id=tx_id,
        )

        # 2) Appeler CinetPay → URL de paiement
        try:
            pay_url = init_payment(
                transaction_id=tx_id,
                amount=product.price_fcfa,
                currency="XOF",
                description=f"Achat {product.title}",
                channels="ALL",
                customer={
                    "id": order.pk,
                    "name": "Client",
                    "surname": "Ebook",
                    "email": order.email,
                    "phone": "+22370000000",
                    "address": "Bamako",
                    "city": "Bamako",
                    "country": "ML",
                },
            )
        except CinetPayError:
            order.status = Order.FAILED
            order.save(update_fields=["status"])
            return render(request, "store/thank_you.html", {"ok": False, "message": "Erreur d'initialisation paiement."})

        return redirect(pay_url)

---

## 4) Retour navigateur (`/payment/return/`)

Dans `store/views.py` :

    from django.views.decorators.http import require_http_methods

    @require_http_methods(["GET", "POST"])
    def payment_return(request):
        # Selon config, CinetPay peut renvoyer transaction_id
        tx_id = request.GET.get("transaction_id") or request.GET.get("order")
        order = Order.objects.filter(cinetpay_payment_id=tx_id).first()
        if not order:
            return render(request, "store/thank_you.html", {"ok": False, "message": "Commande introuvable."})

        if order.status == Order.PAID:
            token, _ = DownloadToken.objects.get_or_create(order=order)
            return render(request, "store/thank_you.html", {"ok": True, "order": order, "token": token})

        # Optionnel : afficher “en cours”, ou re-checker immédiatement (cf. §6)
        return render(request, "store/thank_you.html", {"ok": False, "message": "Paiement en cours de confirmation…"})

---

## 5) Webhook de notification (`/payment/callback/`) + HMAC `x-token`

CinetPay envoie un **POST** (form-data) avec un header `x-token`. Il faut :

1) **Construire** une chaîne en concaténant **dans cet ordre exact** :

- `cpm_site_id`, `cpm_trans_id`, `cpm_trans_date`, `cpm_amount`, `cpm_currency`, `signature`,
  `payment_method`, `cel_phone_num`, `cpm_phone_prefixe`, `cpm_language`, `cpm_version`,
  `cpm_payment_config`, `cpm_page_action`, `cpm_custom`, `cpm_designation`, `cpm_error_message`

2) **Signer** la chaîne avec la **Secret Key** (HMAC-SHA256 → hex)
3) Comparer au header reçu `x-token` avec `hmac.compare_digest`

Dans `store/views.py` :

    import os, hmac, hashlib
    from django.views.decorators.csrf import csrf_exempt
    from django.http import HttpResponse
    from .models import Order, DownloadToken
    from .services.cinetpay import init_payment  # only for context, not used here

    SECRET = os.getenv("CINETPAY_SECRET", "")

    FIELDS_ORDER = [
        "cpm_site_id", "cpm_trans_id", "cpm_trans_date", "cpm_amount", "cpm_currency",
        "signature", "payment_method", "cel_phone_num", "cpm_phone_prefixe", "cpm_language",
        "cpm_version", "cpm_payment_config", "cpm_page_action", "cpm_custom",
        "cpm_designation", "cpm_error_message",
    ]

    def _cinetpay_token(form: dict) -> str:
        data = "".join(form.get(k, "") for k in FIELDS_ORDER)
        return hmac.new(SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()

    @csrf_exempt
    @require_http_methods(["POST"])
    def payment_callback(request):
        received = request.headers.get("x-token", "")
        form = {k: request.POST.get(k, "") for k in FIELDS_ORDER}
        expected = _cinetpay_token(form)

        if not received or not hmac.compare_digest(received, expected):
            return HttpResponse("Invalid signature", status=400)

        tx_id = request.POST.get("cpm_trans_id")
        order = Order.objects.filter(cinetpay_payment_id=tx_id).first()
        if not order:
            return HttpResponse("Order not found", status=404)

        # Recommandé : re-checker l'état réel via l'API (cf. §6) AVANT de livrer
        # (On ne met pas PAID tout de suite ici)
        return HttpResponse("OK")

---

## 6) Vérifier une transaction (API `payment/check`)

Dans `store/services/cinetpay.py` :

    def check_transaction(transaction_id: str) -> dict:
        r = requests.post(f"{API_URL}/v2/payment/check", json={
            "transaction_id": transaction_id,
            "site_id": SITE_ID,
            "apikey": APIKEY,
        }, timeout=20)
        r.raise_for_status()
        return r.json()

Exemple d’usage (dans `payment_callback`, après HMAC OK) :

    from .services.cinetpay import check_transaction

    res = check_transaction(tx_id)
    status_ok = (res.get("code") == "00" and res.get("data", {}).get("status") == "ACCEPTED")

    if status_ok:
        order.status = Order.PAID
        order.save(update_fields=["status"])
        DownloadToken.objects.get_or_create(order=order)
    else:
        order.status = Order.FAILED
        order.save(update_fields=["status"])

---

## 7) Bonnes pratiques

- Créer l’`Order(pending)` **avant** la redirection vers CinetPay.
- Toujours **valider le webhook** (HMAC) **et** faire un `payment/check` avant livraison.
- Logger les notifications et les réponses API (corrélation par `transaction_id`).
- Ne jamais exposer `API_KEY`/`SECRET` côté client ; les stocker en env cPanel.
- S’assurer que `/payment/callback/` est **accessible en HTTPS** depuis Internet.

