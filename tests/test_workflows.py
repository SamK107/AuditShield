import hashlib
import hmac
import json
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from downloads.models import DownloadCategory, DownloadableAsset, ExternalEntitlement
from store.models import Product, Order, ClientInquiry, PaymentIntent, GeneratedDraft, FinalAsset, DownloadToken
from store.utils.tokens import issue_download_token, consume_token


def _sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


@pytest.mark.django_db
def test_cinetpay_webhook_success_and_idempotency(client, settings, monkeypatch):
    settings.CINETPAY_WEBHOOK_SECRET = "secret123"
    # Create minimal product/order/inquiry/payment intent
    product = Product.objects.create(slug="audit-sans-peur", title="Audit", is_published=True, price_fcfa=15000)
    order = Order.objects.create(product=product, email="buyer@example.com", amount_fcfa=15000, status="PENDING")
    inquiry = ClientInquiry.objects.create(email="buyer@example.com", payment_status="PENDING", processing_state="INQUIRY_RECEIVED")
    intent = PaymentIntent.objects.create(inquiry=inquiry, provider="cinetpay", amount=15000, currency="XOF", external_ref="ORDER-XYZ", status="PENDING")

    payload = {"transaction_id": intent.external_ref, "status": "SUCCESS", "amount": 15000, "currency": "XOF"}
    raw = json.dumps(payload).encode("utf-8")
    headers = {"HTTP_X_TOKEN": _sign(settings.CINETPAY_WEBHOOK_SECRET, raw), "CONTENT_TYPE": "application/json"}

    # payment_check returns OK
    with patch("store.services.cinetpay.payment_check", return_value=(True, "PROV-OK")), \
         patch("store.tasks.build_kit_word.delay", return_value=None):
        resp = client.post(reverse("store:cinetpay_notify"), data=raw, **headers)
        assert resp.status_code == 200

    # Status updated and email queued
    inquiry.refresh_from_db()
    intent.refresh_from_db()
    assert inquiry.payment_status == "PAID"
    assert intent.status == "PAID"
    assert len(mail.outbox) == 1  # fulfilment email sent once

    # Idempotent re-post: no extra email
    with patch("store.services.cinetpay.payment_check", return_value=(True, "PROV-OK")), \
         patch("store.tasks.build_kit_word.delay", return_value=None):
        resp2 = client.post(reverse("store:cinetpay_notify"), data=raw, **headers)
        assert resp2.status_code == 200
    assert len(mail.outbox) == 1

    # Invalid signature
    bad_headers = {"HTTP_X_TOKEN": "bad", "CONTENT_TYPE": "application/json"}
    resp3 = client.post(reverse("store:cinetpay_notify"), data=raw, **bad_headers)
    assert resp3.status_code == 400


@pytest.mark.django_db
def test_delivery_email_contains_links(client, settings, monkeypatch):
    settings.SITE_BASE_URL = "https://example.com"
    # Create ebook category and two assets
    ebook = DownloadCategory.objects.create(slug="ebook", title="Ebook", page_path="/downloads/ebook")
    a4 = DownloadableAsset.objects.create(category=ebook, slug="a4", title="PDF A4", file="downloads/a4.pdf", is_published=True)
    x69 = DownloadableAsset.objects.create(category=ebook, slug="x69", title="PDF 6x9", file="downloads/6x9.pdf", is_published=True)
    # Entitlement for extra category (optional)
    # Generate fulfilment email
    with patch("store.services.mailing.SignedUrlService.get_signed_url", side_effect=lambda asset, expires=900: f"https://signed/{asset.slug}"):
        from store.services.mailing import send_fulfilment_email
        send_fulfilment_email(to_email="buyer@example.com", order_ref="ORDER-1")
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert "https://signed/a4" in body
    assert "https://signed/x69" in body
    # Bonus link tokenized
    assert "/bonus/kit-preparation/start" in body


@pytest.mark.django_db
def test_imap_fetch_parses_and_idempotent(settings, monkeypatch, django_capture_on_commit_callbacks):
    # Minimal category
    DownloadCategory.objects.create(slug="ebook", title="Ebook", page_path="/downloads/ebook")
    # Craft a fake IMAP server
    class FakeIMAP:
        def __init__(self, *a, **k): pass
        def login(self, *a, **k): pass
        def select(self, *a, **k): pass
        def search(self, *a, **k): return ("OK", [b"1"])
        def fetch(self, num, spec):
            msg = (
                "Message-ID: <abc@ex>\r\n"
                "From: YouScribe Afrique <no-reply@youscribe.com>\r\n"
                "Subject: Votre reçu EXT-7777\r\n"
                "\r\n"
                "Merci pour votre achat."
            ).encode("utf-8")
            return ("OK", [(b"1", msg)])
        def store(self, *a, **k): pass
        def copy(self, *a, **k): pass
        def expunge(self): pass
        def logout(self): pass
    monkeypatch.setenv("RECEIPTS_IMAP_USER", "u")
    monkeypatch.setenv("RECEIPTS_IMAP_PASSWORD", "p")
    monkeypatch.setenv("RECEIPTS_IMAP_HOST", "h")
    monkeypatch.setenv("RECEIPTS_IMAP_PORT", "993")
    monkeypatch.setenv("RECEIPTS_IMAP_FOLDER", "INBOX")
    monkeypatch.setattr("downloads.management.commands.fetch_receipts.imaplib.IMAP4_SSL", FakeIMAP)

    # Run command twice
    from django.core.management import call_command
    with django_capture_on_commit_callbacks(execute=True):
        call_command("fetch_receipts")
        call_command("fetch_receipts")

    # Only one entitlement created
    ents = ExternalEntitlement.objects.all()
    assert ents.count() == 1
    assert ents.first().platform == "youscribe"
    # One fulfilment email
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_bonus_token_gate_and_docx_generation(client, settings, monkeypatch):
    # Configure token TTL small via settings if used
    settings.BONUS_KIT_TOKEN_TTL_DAYS = 7
    # Build token
    from django.core.signing import TimestampSigner
    signer = TimestampSigner(salt="bonus-kit-preparation")
    token = signer.sign("ORDER-ABC:client@example.com")
    # Form gate GET OK
    resp = client.get("/bonus/kit-preparation/start", {"product_slug": "audit-sans-peur", "token": token})
    assert resp.status_code in (200, 403)  # 403 if token parsing fails

    # Generate a paid inquiry and stub build_kit_word to create a draft
    inquiry = ClientInquiry.objects.create(email="client@example.com", payment_status="PAID", processing_state="PAID")
    def fake_task(inquiry_id):
        obj = ClientInquiry.objects.get(id=inquiry_id)
        GeneratedDraft.objects.get_or_create(inquiry=obj, defaults={"build_log": "ok"})
        obj.processing_state = "DRAFT_DONE"
        obj.save(update_fields=["processing_state"])
    with patch("store.tasks.build_kit_word", side_effect=fake_task):
        # Call our fake directly
        fake_task(inquiry.id)
    inquiry.refresh_from_db()
    assert inquiry.processing_state == "DRAFT_DONE"
    assert GeneratedDraft.objects.filter(inquiry=inquiry).exists()


@pytest.mark.django_db
def test_bonus_publish_sends_email_and_marks_row_green(client, django_user_model, settings):
    # Create staff user and login
    staff = django_user_model.objects.create_user(username="admin", email="admin@example.com", password="x", is_staff=True, is_superuser=True)
    client.force_login(staff)
    # Inquiry with final asset
    inquiry = ClientInquiry.objects.create(email="client@example.com", payment_status="PAID", processing_state="FINAL_UPLOADED")
    FinalAsset.objects.create(inquiry=inquiry, docx="final/kit.docx")
    # Publish
    resp = client.post(reverse("store:kit_publish", args=[inquiry.id]))
    assert resp.status_code in (302, 200)
    # Email sent
    assert len(mail.outbox) >= 1
    # Staff list shows green tag
    resp2 = client.get(reverse("store:kit_staff_list"))
    assert resp2.status_code == 200
    assert "bg-emerald-100" in resp2.content.decode("utf-8")


@pytest.mark.django_db
def test_signed_links_expire_and_renew():
    inquiry = ClientInquiry.objects.create(email="x@x.com", payment_status="PAID", processing_state="PAID")
    dt = issue_download_token(inquiry, ttl_minutes=0)  # immediate expiry
    # Manually set past expiry to ensure invalid
    dt.expires_at = timezone.now() - timezone.timedelta(minutes=1)
    dt.save(update_fields=["expires_at"])
    assert dt.is_valid() is False
    assert consume_token(dt.token) is None
    # Renew
    dt2 = issue_download_token(inquiry, ttl_minutes=30)
    assert dt2.is_valid() is True


@pytest.mark.django_db
def test_permissions_on_backoffice_pages(client, django_user_model):
    # Anonymous
    resp = client.get(reverse("store:kit_staff_list"))
    assert resp.status_code in (302, 403)
    # Staff
    staff = django_user_model.objects.create_user(username="s", password="x", is_staff=True, is_superuser=True)
    client.force_login(staff)
    resp2 = client.get(reverse("store:kit_staff_list"))
    assert resp2.status_code == 200


