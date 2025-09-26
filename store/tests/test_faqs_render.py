# -*- coding: utf-8 -*-
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_product_detail_renders_faq(client):
    """Test que la page product_detail affiche bien la FAQ centralisée."""
    from store.models import Product
    
    # Créer un produit de test
    product = Product.objects.create(
        title="Audit Sans Peur",
        slug="audit-sans-peur",
        subtitle="Guide pratique pour réussir vos audits",
        price_fcfa=25000,
        is_published=True
    )

    url = reverse("store:product_detail", kwargs={"slug": product.slug})
    resp = client.get(url)
    assert resp.status_code == 200

    content = resp.content.decode("utf-8")
    
    # Quelques assertions robustes (extraits de la FAQ)
    assert "FAQ" in content
    assert "À qui s" in content and "adresse cet ebook" in content
    assert "Kit de préparation (1 texte fourni" in content and "3 pages)" in content
    assert "Garantie satisfait ou remboursé de 7 jours" in content
    assert "contact@auditsanspeur.com" in content
    
    # Vérifier que d'autres éléments clés de la FAQ sont présents
    assert "agents publics, gestionnaires financiers" in content
    assert "boîte à outils pratique" in content
    assert "accès au téléchargement est immédiat" in content


def test_faq_content_structure(client):
    """Test que la structure de la FAQ est correctement rendue."""
    from store.models import Product
    
    product = Product.objects.create(
        title="Test Product",
        slug="test-product",
        price_fcfa=10000,
        is_published=True
    )

    url = reverse("store:product_detail", kwargs={"slug": product.slug})
    resp = client.get(url)
    assert resp.status_code == 200

    content = resp.content.decode("utf-8")
    
    # Vérifier la présence des questions principales (parties sans caractères spéciaux)
    expected_question_parts = [
        ("À qui s", "adresse cet ebook"),
        ("Est-ce un manuel", "théorique"),
        ("Comment vais-je recevoir", "après l"),
        ("Quels bonus sont inclus", ""),
        ("version adaptée", "organisation"),
        ("Existe-t-il une garantie", ""),
        ("contacter l", "auteur")
    ]
    
    for part1, part2 in expected_question_parts:
        assert part1 in content, f"Question manquante (partie 1): {part1}"
        if part2:
            assert part2 in content, f"Question manquante (partie 2): {part2}"


def test_faq_accordion_functionality(client):
    """Test que l'accordion Alpine.js est correctement configuré."""
    from store.models import Product
    
    product = Product.objects.create(
        title="Test Product",
        slug="test-product", 
        price_fcfa=15000,
        is_published=True
    )

    url = reverse("store:product_detail", kwargs={"slug": product.slug})
    resp = client.get(url)
    assert resp.status_code == 200

    content = resp.content.decode("utf-8")
    
    # Vérifier que les éléments Alpine.js sont présents
    assert 'x-data="{open:false}"' in content
    assert '@click="open=!open"' in content
    assert 'x-show="open"' in content
    assert 'x-collapse' in content
    
    # Vérifier la structure des icônes Lucide
    assert 'data-lucide="chevron-down"' in content
    assert ':class="{\'rotate-180\':open}"' in content
