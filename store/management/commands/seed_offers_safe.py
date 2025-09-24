from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import OfferTier, Product


class Command(BaseCommand):
    help = (
        "Crée ou met à jour les 3 offres principales (Standard, Kit, Formation) "
        "pour le produit publié."
    )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        product = Product.objects.filter(is_published=True).first()
        if not product:
            self.stdout.write(self.style.WARNING("Aucun product publié."))
            return
        # Upsert par (product, kind) si possible, sinon par title
        tiers_data = [
            {
                "kind": OfferTier.STANDARD,
                "title": "Ebook Audit Sans Peur",
                "cta_type": "BUY",
                "price_fcfa": 15000,
            },
            {
                "kind": OfferTier.PERSONNALISATION,
                "title": "Kit complet de préparation à l’audit",
                "cta_type": "QUOTE",
                "price_fcfa": None,
            },
            {
                "kind": OfferTier.FORMATION,
                "title": "Bouclier contre irrégularité et fautes de gestion",
                "cta_type": "QUOTE",
                "price_fcfa": None,
            },
        ]
        created, updated = 0, 0
        for data in tiers_data:
            tier, exists = OfferTier.objects.get_or_create(
                product=product,
                kind=data["kind"],
                defaults=data,
            )
            if not exists:
                for k, v in data.items():
                    setattr(tier, k, v)
                tier.save()
                updated += 1
            else:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Tiers créés: {created}, mis à jour: {updated}"
            )
        )
