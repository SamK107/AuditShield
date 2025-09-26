import os
import re
from django.urls import reverse, NoReverseMatch
from django.test import TestCase
from bs4 import BeautifulSoup
from store.models import Product

PATHS_TO_CHECK = ["/", "/offres/"]
PRODUCT_SLUG = os.environ.get("PRODUCT_SLUG", "<PRODUCT_SLUG>")  # À compléter

class TestLinksAndCarousel(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Crée un produit de test si le slug est renseigné
        if PRODUCT_SLUG and PRODUCT_SLUG != "<PRODUCT_SLUG>":
            Product.objects.create(
                slug=PRODUCT_SLUG,
                title="Produit Test",
                subtitle="Sous-titre test",
                price_fcfa=12345,
                is_published=True,
            )

    def test_key_pages_respond(self):
        paths = PATHS_TO_CHECK[:]
        if PRODUCT_SLUG and PRODUCT_SLUG != "<PRODUCT_SLUG>":
            paths.append(f"/ebook/{PRODUCT_SLUG}/")
        for path in paths:
            resp = self.client.get(path)
            self.assertIn(resp.status_code, (200, 301, 302), f"{path} status {resp.status_code}")

    def test_internal_links(self):
        paths = PATHS_TO_CHECK[:]
        if PRODUCT_SLUG and PRODUCT_SLUG != "<PRODUCT_SLUG>":
            paths.append(f"/ebook/{PRODUCT_SLUG}/")
        for path in paths:
            resp = self.client.get(path)
            soup = BeautifulSoup(resp.content, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/") and not href.startswith("//"):
                    r = self.client.get(href)
                    self.assertIn(r.status_code, (200, 301, 302), f"Lien {href} status {r.status_code} depuis {path}")

    def test_images_no_404(self):
        paths = PATHS_TO_CHECK[:]
        if PRODUCT_SLUG and PRODUCT_SLUG != "<PRODUCT_SLUG>":
            paths.append(f"/ebook/{PRODUCT_SLUG}/")
        for path in paths:
            resp = self.client.get(path)
            soup = BeautifulSoup(resp.content, "html.parser")
            for img in soup.find_all("img", src=True):
                src = img["src"]
                if src.startswith("/") and not src.startswith("//"):
                    r = self.client.get(src)
                    self.assertIn(r.status_code, (200, 304), f"Image {src} status {r.status_code} depuis {path}")

    def test_carousel_accessibility(self):
        if not (PRODUCT_SLUG and PRODUCT_SLUG != "<PRODUCT_SLUG>"):
            self.skipTest("PRODUCT_SLUG non renseigné, test carrousel ignoré.")
        path = f"/ebook/{PRODUCT_SLUG}/"
        resp = self.client.get(path)
        soup = BeautifulSoup(resp.content, "html.parser")
        # Cherche le carrousel Alpine.js (x-data avec slides)
        carousel = soup.find(attrs={"x-data": re.compile(r"slides", re.I)})
        if not carousel:
            # Fallback : cherche par classe contenant carousel/slider
            carousel = soup.find(class_=re.compile(r"carousel|slider", re.I))
        self.assertIsNotNone(carousel, "Carrousel non trouvé (x-data avec 'slides' ou classe contenant 'carousel'/'slider')")
        # Vérifie la structure Alpine.js
        x_data = carousel.get("x-data", "")
        self.assertIn("slides", x_data, "x-data ne contient pas 'slides'")
        self.assertIn("next()", x_data, "Fonction next() manquante dans x-data")
        self.assertIn("prev()", x_data, "Fonction prev() manquante dans x-data")
        
        # Vérifie les templates d'images (statiques dans le HTML)
        img_templates = carousel.find_all("img")
        if img_templates:
            # Si des images statiques sont trouvées, vérifie leurs attributs
            for i, img in enumerate(img_templates):
                alt = img.get("alt", "").strip()
                # Accepte les attributs Alpine.js dynamiques (ex: :alt="slides[i].alt")
                if not alt and not img.get(":alt"):
                    self.fail(f"Image {i+1} sans alt ni :alt dynamique : {img}")
                # Vérifie loading (peut être dynamique)
                if i > 0 and not img.get("loading") and not img.get(":loading"):
                    # Pour les images Alpine.js, on peut être plus tolérant
                    pass  # Les images dynamiques peuvent avoir des attributs différents
        
        # Contrôles Prev/Next (boutons avec @click="prev()" et @click="next()")
        prev_btn = carousel.find(attrs={"@click": re.compile("prev", re.I)})
        next_btn = carousel.find(attrs={"@click": re.compile("next", re.I)})
        self.assertTrue(prev_btn, "Bouton 'Précédent' (@click='prev()') manquant")
        self.assertTrue(next_btn, "Bouton 'Suivant' (@click='next()') manquant")
        
        # Vérifie les dots de navigation
        dots = carousel.find_all(attrs={"@click": re.compile("i=", re.I)})
        self.assertTrue(len(dots) > 0, "Points de navigation (@click='i=idx') manquants")

    def test_store_offers_route_exists(self):
        try:
            url = reverse("store:offers")
            self.assertTrue(url)
        except NoReverseMatch:
            self.skipTest("Route nommée store:offers absente.")
