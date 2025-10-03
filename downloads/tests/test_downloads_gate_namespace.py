import pytest
from django.urls import reverse
from downloads.models import DownloadCategory, DownloadEntitlement

@pytest.mark.django_db
 def test_redirects_to_claim_when_protected(client):
     # bonus doit être protégé (migration + seed)
     cat = DownloadCategory.objects.get(slug="bonus")
     assert cat.is_protected and cat.required_sku == "EBOOK_ASP"
     url = reverse("downloads:category_bonus")
     resp = client.get(url, follow=False)
     assert resp.status_code in (301, 302)
     # Expect redirection to the public claim form
     assert reverse("downloads_public:claim_access") in resp["Location"]

@pytest.mark.django_db
 def test_access_with_session_email_entitlement(client):
     cat = DownloadCategory.objects.get(slug="checklists")
     DownloadEntitlement.objects.create(email="x@y.z", sku="EBOOK_ASP")
     session = client.session
     session["download_claim_email"] = "x@y.z"
     session.save()
     url = reverse("downloads:category_checklists")
     resp = client.get(url)
     assert resp.status_code == 200
