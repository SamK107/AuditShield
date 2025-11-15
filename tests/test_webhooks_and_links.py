import hashlib
import hmac
import os

import pytest

from store.services.cinetpay import verify_signature
from security.links import issue_bonus_start_link


def test_cinetpay_verify_signature_ok(monkeypatch):
    secret = "test_secret_123"
    monkeypatch.setenv("CINETPAY_WEBHOOK_SECRET", secret)
    body = b'{"transaction_id":"ORDER-ABC","status":"SUCCESS"}'
    sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    assert verify_signature(sig, body) is True
    assert verify_signature("sha256=" + sig, body) is True


def test_bonus_issue_link_contains_token(settings):
    settings.SITE_BASE_URL = "https://example.com"
    url = issue_bonus_start_link(order_ref="ORD-123", email="a@b.com", base_url=settings.SITE_BASE_URL)
    assert url.startswith("https://example.com/bonus/kit-preparation/start")
    assert "token=" in url


