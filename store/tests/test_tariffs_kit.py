from django.test import TestCase
from django.urls import reverse


class TariffsKitPageTests(TestCase):
    def test_tariffs_page_renders(self):
        url = reverse("store:tariffs_kit")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode("utf-8")
        # Palier names
        self.assertIn("Essentiel+", content)
        self.assertIn("Complet Pro", content)
        self.assertIn("Expert Audit", content)
        # CTA to kit inquiry
        self.assertIn(reverse("store:kit_inquiry"), content)

    def test_estimate_api_complete_pro(self):
        url = reverse("store:estimate_kit")
        resp = self.client.get(url, {"n_docs": 5})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("tier_code"), "complete_pro")



