from django.core.management.base import BaseCommand

from store.models import OfferTier, Product


class Command(BaseCommand):
    help = "Seed produit/tiers/exemples"

    def handle(self, *args, **options):
        product, _ = Product.objects.get_or_create(
            slug="audit-services-publics",
            defaults=dict(
                title="Ebook - Audit Sans Peur",
                subtitle="Le guide concret pour éviter les mauvaises surprises.",
                price_fcfa=15000,
                guarantee_text="Satisfait ou remboursé 7 jours.",
                faq_json=[
                    {
                        "q": "Format et mises à jour ?",
                        "a": "PDF, mises à jour incluses pendant 3 mois.",
                    },
                    {
                        "q": "Remboursement ?",
                        "a": "Oui, sous 7 jours si le contenu ne vous aide pas.",
                    },
                ],
                social_proofs_json=[
                    {"t": "Directeur Financier", "q": "Clair et actionnable."},
                    {"t": "Auditeur Interne", "q": "Nous a fait gagner des semaines."},
                ],
                is_published=True,
            ),
        )

        # Offres
        OfferTier.objects.get_or_create(
            product=product,
            kind=OfferTier.STANDARD,
            defaults=dict(
                price_fcfa=15000,
                description_md="Ebook + Dossier irrégularités (1 texte) + Guide 7 étapes.",
                cta_type="BUY",
            ),
        )
        OfferTier.objects.get_or_create(
            product=product,
            kind=OfferTier.PERSONNALISATION,
            defaults=dict(
                price_fcfa=None,
                description_md=(
                    "Adaptation à votre structure (textes, organisation, circuits). "
                    "Prix au nombre de pages traitées."
                ),
                cta_type="QUOTE",
            ),
        )
        OfferTier.objects.get_or_create(
            product=product,
            kind=OfferTier.FORMATION,
            defaults=dict(
                price_fcfa=None,
                description_md="Cas pratiques, cahier du participant, assistance au suivi des recommandations.",
                cta_type="CALL",
            ),
        )

        self.stdout.write(self.style.SUCCESS("Seed OK."))
