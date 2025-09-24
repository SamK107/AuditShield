import os
import time
import hmac
import json
import hashlib
import requests
import base64
from django.core.management.base import BaseCommand, CommandError

DEFAULT_URL = "http://127.0.0.1:8000/payment/callback/"
DEFAULT_HEADER = os.getenv("CINETPAY_WEBHOOK_HEADER", "x-token")

def _make_signature(secret: str, raw: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()

class Command(BaseCommand):
    help = "Simule l'envoi du webhook CinetPay vers /payment/callback/ pour les tests locaux."

    def add_arguments(self, parser):
        parser.add_argument("--url", default=DEFAULT_URL, help="URL du callback (defaut: http://127.0.0.1:8000/payment/callback/)")
        parser.add_argument("--order", required=True, help="Order ID (ex: ORD-TEST-001)")
        parser.add_argument("--status", choices=["PAID", "FAILED"], default="PAID", help="Statut simulé")
        parser.add_argument("--signature", choices=["ok", "bad"], default="ok", help="Signature HMAC simulée")
        parser.add_argument("--repeat", type=int, default=1, help="Nombre d'envois")
        parser.add_argument("--delay", type=float, default=0.0, help="Délai (s) entre envois")
        parser.add_argument("--amount", type=int, default=15000, help="Montant simulé")
        parser.add_argument("--currency", default="XOF", help="Devise simulée (defaut: XOF)")
        parser.add_argument("--method", default="CREDIT_CARD", help="Moyen de paiement simulé")
        parser.add_argument("--algo", choices=["hex","b64","hexpref"], default="hex", help="HMAC signature format")

    def handle(self, *args, **opts):
        url = opts["url"]
        order = opts["order"]
        status = opts["status"]
        sign_mode = opts["signature"]
        repeat = max(1, opts["repeat"])
        delay = max(0.0, opts["delay"])
        amount = opts["amount"]
        currency = opts["currency"]
        method = opts["method"]

        secret = os.getenv("CINETPAY_WEBHOOK_SECRET")
        if sign_mode == "ok" and not secret:
            raise CommandError("CINETPAY_WEBHOOK_SECRET non défini dans l'environnement.")

        payload = {
            "cpm_trans_id": order,
            "order_id": order,
            "status": status,
            "amount": amount,
            "currency": currency,
            "payment_method": method,
            "metadata": {"simulated": True},
        }

        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        if sign_mode == "ok":
            digest = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
            if opts["algo"] == "hex":
                sigval = digest.hex()
            elif opts["algo"] == "b64":
                sigval = base64.b64encode(digest).decode()
            else:  # hexpref
                sigval = f"sha256={digest.hex()}"
            headers[DEFAULT_HEADER] = sigval
        else:
            headers[DEFAULT_HEADER] = "invalid-signature"

        for i in range(repeat):
            try:
                resp = requests.post(url, data=raw, headers=headers, timeout=10)
                self.stdout.write(self.style.SUCCESS(f"[{i+1}/{repeat}] {resp.status_code} {resp.text[:200]}"))
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f"[{i+1}/{repeat}] ERREUR réseau: {e}"))
            if i < repeat - 1 and delay > 0:
                time.sleep(delay)
