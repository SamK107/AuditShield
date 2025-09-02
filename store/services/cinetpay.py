# store/services/cinetpay.py
import os, requests
from urllib.parse import urlencode

API_URL = os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com")
APIKEY  = os.getenv("CINETPAY_API_KEY")
SITE_ID = os.getenv("CINETPAY_SITE_ID")
RETURN_URL = os.getenv("CINETPAY_RETURN_URL")
NOTIFY_URL = os.getenv("CINETPAY_NOTIFY_URL")

class CinetPayError(Exception):
    pass

def init_payment(transaction_id: str, amount: int, currency: str, description: str,
                 channels: str = "ALL", customer: dict | None = None) -> str:
    """Appel réel à CinetPay pour créer une transaction."""
    payload = {
        "apikey": APIKEY,
        "site_id": SITE_ID,
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
        "description": description,
        "notify_url": NOTIFY_URL,
        "return_url": RETURN_URL,
        "channels": channels,
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
            "customer_country": customer.get("country"),
            "customer_state": customer.get("state", ""),
            "customer_zip_code": customer.get("zip", "00000"),
        })

    r = requests.post(f"{API_URL}/v2/payment", json=payload, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("code") != "201":
        raise CinetPayError(f"Init failed: {data}")
    return data["data"]["payment_url"]

def check_transaction(transaction_id: str) -> dict:
    r = requests.post(f"{API_URL}/v2/payment/check", json={
        "transaction_id": transaction_id,
        "site_id": SITE_ID,
        "apikey": APIKEY,
    }, timeout=20)
    r.raise_for_status()
    return r.json()

# --- Helpers ---

def init_payment_auto(*, order, request):
    """
    Si les variables CinetPay ne sont pas configurées (dev),
    on renvoie une URL de retour "mock" pour simuler un succès.
    Sinon, on appelle l'API réelle.
    """
    missing = not (APIKEY and SITE_ID and RETURN_URL and NOTIFY_URL)
    if missing:
        params = urlencode({"status": "success", "order": str(order.order_id)})
        return f"/payment/return/?{params}"
    return init_payment(
        transaction_id=order.cinetpay_payment_id,
        amount=order.amount_fcfa,
        currency="XOF",
        description=f"Achat {order.product.title}",
        channels="ALL",
        customer={
            "id": order.pk,
            "name": "Client",
            "surname": "Ebook",
            "email": order.email,
        },
    )

def safe_check(transaction_id: str) -> dict:
    """Renvoie un dict status-like même en dev (sans API)."""
    if not (APIKEY and SITE_ID):
        # En dev sans clés, considérer comme accepté pour test
        return {"code": "00", "data": {"status": "ACCEPTED"}}
    return check_transaction(transaction_id)
