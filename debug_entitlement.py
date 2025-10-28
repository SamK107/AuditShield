#!/usr/bin/env python
"""Script de diagnostic pour vérifier les entitlements"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from downloads.models import ExternalEntitlement

print("=== Diagnostic EXT-7777 ===")
order_ref = "EXT-7777"
email = "aloubs700@gmail.com"

# Recherche exacte
print(f"\nRecherche: order_ref='{order_ref}', email='{email}'")
exact_match = ExternalEntitlement.objects.filter(
    order_ref__iexact=order_ref,
    email__iexact=email,
)
print(f"Résultats exacts: {exact_match.count()}")
for e in exact_match:
    print(f"  - {e.order_ref} | {e.email} | {e.category.slug}")

# Recherche avec catégorie ebook
print(f"\nRecherche avec catégorie 'ebook':")
ebook_match = ExternalEntitlement.objects.filter(
    order_ref__iexact=order_ref,
    email__iexact=email,
    category__slug="ebook",
)
print(f"Résultats avec catégorie ebook: {ebook_match.count()}")
for e in ebook_match:
    print(f"  - {e.order_ref} | {e.email} | {e.category.slug}")

# Recherche partielle
print(f"\nTous les entitlements contenant EXT-7777:")
partial = ExternalEntitlement.objects.filter(
    order_ref__icontains="EXT-7777"
)
print(f"Résultats partiels: {partial.count()}")
for e in partial:
    print(f"  - {e.order_ref} | {e.email} | {e.category.slug}")

# Tous les entitlements pour cet email
print(f"\nTous les entitlements pour {email}:")
email_match = ExternalEntitlement.objects.filter(
    email__iexact=email
)
print(f"Résultats pour email: {email_match.count()}")
for e in email_match:
    print(f"  - {e.order_ref} | {e.email} | {e.category.slug}")

