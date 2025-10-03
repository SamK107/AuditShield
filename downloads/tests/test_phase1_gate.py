import pytest
from django.urls import reverse
from downloads.models import DownloadCategory, DownloadEntitlement

@pytest.mark.django_db
def test_protected_category_redirects_to_claim(client):
    cat = DownloadCategory.objects.get(slug="bonus")
    assert cat.is_protected and cat.required_sku == "EBOOK_ASP"
    resp = client.get(reverse("downloads:category_bonus"))
    assert resp.status_code == 302
    assert "claim" in resp["Location"]

@pytest.mark.django_db
def test_email_entitlement_grants_access(client):
    cat = DownloadCategory.objects.get(slug="checklists")
    DownloadEntitlement.objects.create(email="x@y.z", sku="EBOOK_ASP")
    session = client.session
    session["download_claim_email"] = "x@y.z"
    session.save()
    resp = client.get(reverse("downloads:category_checklists"))
    assert resp.status_code == 200
    assert b"downloads" in resp.content.lower()
