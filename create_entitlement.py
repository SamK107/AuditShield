#!/usr/bin/env python
"""Script pour créer ou vérifier un entitlement"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from downloads.models import ExternalEntitlement, DownloadCategory

# Paramètres
order_ref = "EXT-7777"
email = "aloubs700@gmail.com"
category_slug = "ebook"

print(f"=== Vérification/Création entitlement ===")
print(f"Order Ref: {order_ref}")
print(f"Email: {email}")
print(f"Category: {category_slug}")
print()

# Vérifier si la catégorie existe
category = DownloadCategory.objects.filter(slug=category_slug).first()
if not category:
    print(f"❌ Catégorie '{category_slug}' introuvable !")
    print("Catégories disponibles:")
    for cat in DownloadCategory.objects.all():
        print(f"  - {cat.slug} ({cat.title})")
    exit(1)

print(f"✅ Catégorie trouvée: {category.title}")
print()

# Vérifier les entitlements existants
print("=== Entitlements existants (toutes catégories) ===")
existing = ExternalEntitlement.objects.filter(
    order_ref__iexact=order_ref,
    email__iexact=email
)
print(f"Nombre trouvé: {existing.count()}")
for e in existing:
    print(f"  - {e.order_ref} | {e.email} | {e.category.slug} | {e.platform}")
print()

# Vérifier spécifiquement la catégorie ebook
ebook_match = ExternalEntitlement.objects.filter(
    order_ref__iexact=order_ref,
    email__iexact=email,
    category__slug=category_slug
).first()

if ebook_match:
    print(f"✅ Entitlement EXISTE déjà pour la catégorie '{category_slug}':")
    print(f"   ID: {ebook_match.id}")
    print(f"   Créé le: {ebook_match.created_at}")
else:
    print(f"⚠️  Entitlement MANQUANT pour la catégorie '{category_slug}'")
    print("   Création automatique en cours...")
    try:
        ent, created = ExternalEntitlement.objects.get_or_create(
            email=email,
            category=category,
            platform="external",
            order_ref=order_ref,
            defaults={}
        )
        if created:
            print(f"✅ Entitlement créé avec succès !")
            print(f"   ID: {ent.id}")
            print(f"   Email: {ent.email}")
            print(f"   Référence: {ent.order_ref}")
            print(f"   Catégorie: {ent.category.slug}")
        else:
            print(f"ℹ️  Entitlement existait déjà")
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        import traceback
        traceback.print_exc()

