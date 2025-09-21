import os

import pytest

cinetpay = pytest.importorskip("store.services.cinetpay")

def test_cinetpay_config_defaults(monkeypatch):
    monkeypatch.setenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com")
    assert cinetpay.API_URL.startswith("https://")

def test_cinetpay_post_is_mockable(requests_mock):
    base = os.getenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com")
    endpoint = f"{base}/charge"
    requests_mock.post(endpoint, json={"code": "201", "message": "OK"})
    payload = {"amount": 15000, "currency": "XOF"}

    # cinetpay._post expects a path like "/charge"
    res = cinetpay._post("/charge", payload)
    assert str(res.get("code")) in ("201", "00", "SUCCESS")
