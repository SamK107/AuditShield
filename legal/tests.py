from django.test import TestCase
from django.urls import reverse

from legal.models import LegalDocument


class LegalPagesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Supprimer les documents existants pour éviter les conflits d'unicité
        LegalDocument.objects.filter(slug__in=["mentions-legales", "privacy", "cookies"]).delete()
        LegalDocument.objects.create(
            title="Mentions légales",
            slug="mentions-legales",
            doc_type="mentions",
            html_content="<p>Éditeur : Bloom Shield Gouvernance</p>",
            status="published",
        )
        LegalDocument.objects.create(
            title="Politique de confidentialité",
            slug="privacy",
            doc_type="privacy",
            html_content="<p>Nous collectons les données nécessaires.</p>",
            status="published",
        )
        LegalDocument.objects.create(
            title="Politique Cookies",
            slug="cookies",
            doc_type="cookies",
            html_content="<p>Cookies nécessaires et mesure d’audience.</p>",
            status="published",
        )

    def test_mentions_page(self):
        url = reverse("legal:mentions")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Mentions légales")

    def test_privacy_page(self):
        url = reverse("legal:privacy")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Politique de confidentialité")

    def test_cookies_page(self):
        url = reverse("legal:cookies")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Politique Cookies")

    def test_mentions_modal_partial(self):
        url = reverse("legal:mentions_modal")
        resp = self.client.get(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Mentions légales")
