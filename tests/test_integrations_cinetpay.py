import os
from unittest.mock import patch, Mock
import pytest

cinetpay = pytest.importorskip("store.services.cinetpay")

def test_cinetpay_config_defaults(monkeypatch):
    monkeypatch.setenv("CINETPAY_API_URL", "https://api-checkout.cinetpay.com")
    assert cinetpay.API_URL.startswith("https://")

@pytest.mark.parametrize("code", ["201", "00", "SUCCESS"])
def test_cinetpay_post_is_mockable(code):
    payload = {"amount": 15000, "currency": "XOF"}
    with patch("store.services.cinetpay.requests.post") as mock_post:
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.text = '{"code": "%s"}' % code
        mock_resp.json.return_value = {"code": code, "message": "OK"}
        mock_resp.raise_for_status = Mock()
        mock_post.return_value = mock_resp
        res = cinetpay._post("/charge", payload)
        assert str(res.get("code")).upper() in ("201", "00", "SUCCESS")
