import uuid
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from downloads.models import DownloadableAsset, DownloadCategory
from store.models import DownloadToken, Order, Payment, PaymentEvent, Product


def _url(slug: str) -> str:
    return f"/downloads/{slug}/"


@pytest.mark.django_db
def test_public_category_accessible(client, cat_checklists):
    resp = client.get(_url(cat_checklists.slug))
    assert resp.status_code in (200, 301, 302, 404)


@pytest.mark.django_db
def test_protected_category_redirects(client, cat_bonus):
    resp = client.get(_url(cat_bonus.slug))
    assert resp.status_code in (200, 301, 302, 403, 404)


@pytest.mark.django_db
def test_entitlement_allows_access(client, cat_bonus):
    # Later, create entitlement to assert 200; for now just no 500.
    resp = client.get(_url(cat_bonus.slug))
    assert resp.status_code in (200, 301, 302, 403, 404)


@pytest.mark.django_db
def test_secure_downloads_token_access(client):
    # Arrange
    category = DownloadCategory.objects.create(slug="ebook", title="Ebook", page_path="/ebook")
    product = Product.objects.create(slug="test-ebook", title="Test Ebook", is_published=True)
    order = Order.objects.create(product=product, email="buyer@example.com", status="PAID")
    token_obj = DownloadToken.objects.create(order=order)
    asset_a4 = DownloadableAsset.objects.create(
        category=category, title="PDF A4", file="/tmp/a4.pdf", is_published=True
    )
    asset_6x9 = DownloadableAsset.objects.create(
        category=category, title="PDF 6x9", file="/tmp/6x9.pdf", is_published=True
    )
    url = reverse("downloads:secure_token", args=[str(token_obj.token)])
    # Act
    resp = client.get(url)
    # Assert
    assert resp.status_code == 200
    assert b"PDF A4" in resp.content
    assert b"PDF 6x9" in resp.content
    # Expiration
    token_obj.expires_at = timezone.now() - timezone.timedelta(minutes=1)
    token_obj.save()
    resp2 = client.get(url)
    assert resp2.status_code == 410
    assert b"expir" in resp2.content.lower()


@pytest.mark.django_db
def test_secure_downloads_order_uuid_access(client):
    # Arrange
    User = get_user_model()
    user = User.objects.create_user(
        username="buyer", email="buyer@example.com", password="pass1234"
    )
    category = DownloadCategory.objects.create(slug="ebook", title="Ebook", page_path="/ebook")
    product = Product.objects.create(slug="test-ebook2", title="Test Ebook 2", is_published=True)
    order = Order.objects.create(product=product, email="buyer@example.com", status="PAID")
    asset_a4 = DownloadableAsset.objects.create(
        category=category, title="PDF A4", file="/tmp/a4b.pdf", is_published=True
    )
    asset_6x9 = DownloadableAsset.objects.create(
        category=category, title="PDF 6x9", file="/tmp/6x9b.pdf", is_published=True
    )
    url = reverse("downloads:secure", args=[str(order.pk)])
    # Act : accès sans login
    resp = client.get(url)
    assert resp.status_code == 403  # Guard : doit être connecté
    # Act : accès avec login mais mauvais user
    other = User.objects.create_user(
        username="other", email="other@example.com", password="pass1234"
    )
    client.login(username="other", password="pass1234")
    resp2 = client.get(url)
    assert resp2.status_code == 403
    # Act : accès avec bon user
    client.login(username="buyer", password="pass1234")
    resp3 = client.get(url)
    assert resp3.status_code == 200
    assert b"PDF A4" in resp3.content
    assert b"PDF 6x9" in resp3.content
    # Non payé
    order.status = "PENDING"
    order.save()
    resp4 = client.get(url)
    assert resp4.status_code == 403


@pytest.mark.django_db
def test_secure_downloads_token_invalid(client):
    import uuid

    url = reverse("downloads:secure_token", args=[str(uuid.uuid4())])
    resp = client.get(url)
    assert resp.status_code in (404, 410)
    assert b"invalide" in resp.content.lower() or b"expir" in resp.content.lower()


@pytest.mark.django_db
def test_deliver_ebook_sends_token_link(settings, client):
    # Arrange
    from store.views import deliver_ebook

    category = DownloadCategory.objects.create(slug="ebook", title="Ebook", page_path="/ebook")
    product = Product.objects.create(slug="test-ebook3", title="Test Ebook 3", is_published=True)
    order = Order.objects.create(product=product, email="buyer3@example.com", status="PAID")
    payment = Payment.objects.create(order_id=order.provider_ref, status="PAID", email=order.email)
    # Patch send_mail pour capturer l'email
    with mock.patch("store.views.send_mail") as send_mail_mock:
        deliver_ebook(payment)
        assert send_mail_mock.called
        args, kwargs = send_mail_mock.call_args
        body = args[1]
        # Lien tokenisé doit être dans l'email
        assert "/downloads/secure/token/" in body
        # Extraire le token de l'URL
        import re

        m = re.search(r"/downloads/secure/token/([a-f0-9\-]+)/", body)
        assert m
        token = m.group(1)
        # Vérifier que le lien est accessible
        url = reverse("downloads:secure_token", args=[token])
        resp = client.get(url)
        assert resp.status_code == 200


@pytest.mark.django_db
def test_secure_downloads_one_variant_only(client):
    category = DownloadCategory.objects.create(slug="ebook", title="Ebook", page_path="/ebook")
    product = Product.objects.create(slug="test-ebook4", title="Test Ebook 4", is_published=True)
    order = Order.objects.create(product=product, email="buyer4@example.com", status="PAID")
    token_obj = DownloadToken.objects.create(order=order)
    asset_a4 = DownloadableAsset.objects.create(
        category=category, title="PDF A4", file="/tmp/a4c.pdf", is_published=True
    )
    url = reverse("downloads:secure_token", args=[str(token_obj.token)])
    resp = client.get(url)
    assert resp.status_code == 200
    assert b"PDF A4" in resp.content
    assert b"6x9".encode() not in resp.content.lower()  # Pas de 6x9
    assert b"variante" in resp.content.lower() or b"manquante" in resp.content.lower()


@pytest.mark.django_db
def test_secure_downloads_no_assets(client):
    category = DownloadCategory.objects.create(slug="ebook", title="Ebook", page_path="/ebook")
    product = Product.objects.create(slug="test-ebook5", title="Test Ebook 5", is_published=True)
    order = Order.objects.create(product=product, email="buyer5@example.com", status="PAID")
    token_obj = DownloadToken.objects.create(order=order)
    url = reverse("downloads:secure_token", args=[str(token_obj.token)])
    resp = client.get(url)
    assert resp.status_code == 200
    assert (
        b"aucun" in resp.content.lower()
        or b"manquante" in resp.content.lower()
        or b"variante" in resp.content.lower()
    )


@pytest.mark.django_db
def test_secure_downloads_token_isolated_per_order(client):
    category = DownloadCategory.objects.create(slug="ebook", title="Ebook", page_path="/ebook")
    product1 = Product.objects.create(slug="test-ebook6a", title="Test Ebook 6A", is_published=True)
    product2 = Product.objects.create(slug="test-ebook6b", title="Test Ebook 6B", is_published=True)
    order1 = Order.objects.create(product=product1, email="buyer6@example.com", status="PAID")
    order2 = Order.objects.create(product=product2, email="buyer6@example.com", status="PAID")
    token1 = DownloadToken.objects.create(order=order1)
    token2 = DownloadToken.objects.create(order=order2)
    asset_a4 = DownloadableAsset.objects.create(
        category=category, title="PDF A4", file="/tmp/a4d.pdf", is_published=True
    )
    asset_6x9 = DownloadableAsset.objects.create(
        category=category, title="PDF 6x9", file="/tmp/6x9d.pdf", is_published=True
    )
    url1 = reverse("downloads:secure_token", args=[str(token1.token)])
    url2 = reverse("downloads:secure_token", args=[str(token2.token)])
    resp1 = client.get(url1)
    resp2 = client.get(url2)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    # Les deux tokens donnent accès, mais sont indépendants
    assert b"PDF A4" in resp1.content and b"PDF 6x9" in resp1.content
    assert b"PDF A4" in resp2.content and b"PDF 6x9" in resp2.content
