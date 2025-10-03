import pytest
from django.urls import reverse
from downloads.models import DownloadCategory, DownloadEntitlement

@pytest.mark.django_db
def test_bonus_redirects_to_claim_when_no_access(client):
    cat = DownloadCategory.objects.get(slug="bonus")
    assert cat.is_protected is True
    url = reverse("downloads_public:category_bonus")
    resp = client.get(url, follow=False)
    assert resp.status_code in (301, 302)
    assert reverse("downloads_public:claim_access") in resp["Location"]

@pytest.mark.django_db
def test_access_unlocked_after_claim_creates_entitlements(client):
    cat = DownloadCategory.objects.get(slug="bonus")
    DownloadEntitlement.objects.create(email="x@y.z", sku="EBOOK_ASP")
    session = client.session
    session["download_claim_email"] = "x@y.z"
    session.save()
    url = reverse("downloads_public:category_bonus")
    resp = client.get(url)
    assert resp.status_code == 200


