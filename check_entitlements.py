#!/usr/bin/env python
"""Script temporaire pour vérifier les entitlements"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from downloads.models import ExternalEntitlement

print("=== Entitlements existants ===")
print(f"Total: {ExternalEntitlement.objects.count()}\n")

for e in ExternalEntitlement.objects.all().order_by('-created_at'):
    print(f"- Référence: {e.order_ref or '(vide)'}")
    print(f"  Email: {e.email}")
    print(f"  Catégorie: {e.category.slug}")
    print(f"  Plateforme: {e.platform}")
    print(f"  Créé le: {e.created_at}")
    print()

# Vérifier spécifiquement EXT-7777
print("\n=== Vérification EXT-7777 ===")
ext_7777 = ExternalEntitlement.objects.filter(order_ref__iexact="EXT-7777")
if ext_7777.exists():
    for e in ext_7777:
        print(f"✅ Trouvé: {e.order_ref} | {e.email} | {e.category.slug}")
else:
    print("❌ EXT-7777 n'existe pas encore dans la base")

