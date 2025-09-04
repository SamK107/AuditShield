# store/management/commands/seed_store.py
from django.core.management.base import BaseCommand
from store.models import Product, OfferTier, ExampleSlide, MediaAsset, IrregularityCategory, IrregularityRow

class Command(BaseCommand):
    help = "Seed produit/tiers/exemples + catégories & lignes (DFM)"

    def handle(self, *args, **options):
        product, _ = Product.objects.get_or_create(
            slug="audit-services-publics",
            defaults=dict(
                title="Audit des services publics",
                subtitle="Le guide concret pour éviter les mauvaises surprises.",
                price_fcfa=15000,
                guarantee_text="Satisfait ou remboursé 7 jours.",
                faq_json=[{"q":"Format ?","a":"PDF; mises à jour 3 mois."}],
                social_proofs_json=[{"t":"DAF","q":"Très concret."}],
                is_published=True,
            ),
        )

        # Offres (minimal)
        OfferTier.objects.get_or_create(product=product, kind="STANDARD", defaults=dict(
            price_fcfa=15000, description_md="Ebook + Dossier irrégularités (1 texte) + Guide 7 étapes.", cta_type="BUY"
        ))

        # Slides d'exemples (1 par défaut)
        ExampleSlide.objects.get_or_create(product=product, title="Rapprochement bancaire tardif", defaults=dict(
            irregularity="Rapprochements effectués hors délais.",
            indicators="Absence de signatures, écarts non justifiés.",
            legal_ref="Réglementation comptable secteur public.",
            remedy="Rapprochement mensuel signé; justification des écarts.",
            risks="Erreurs non détectées, risque de fraude.",
        ))

        # Catégorie : DFM (STRUCTURE)
        dfm, _ = IrregularityCategory.objects.get_or_create(
            product=product, slug="dfm",
            defaults=dict(title="Direction des finances et du matériel (DFM)", group="STRUCTURE", order=0)
        )

        rows = [
            dict(irregularity="Rapprochements bancaires non réalisés",
                 reference="SYSCOHADA 2017, PCG § Trésorerie",
                 actors="DFM, comptable",
                 dispositions="Vérifier chaque mois, signatures du DFM et ordonnateur"),
            dict(irregularity="Dépenses hors crédits disponibles",
                 reference="Loi de finances nationale",
                 actors="Ordonnateur, contrôleur financier",
                 dispositions="Contrôle des engagements avant ordonnancement"),
            dict(irregularity="Justificatifs incomplets (factures sans PV)",
                 reference="Décret marchés publics",
                 actors="DFM, service marchés",
                 dispositions="Dossier complet = contrat + PV + facture"),
        ]
        for i, data in enumerate(rows):
            IrregularityRow.objects.get_or_create(
                category=dfm, version="EBOOK", order=i, defaults=data
            )

        self.stdout.write(self.style.SUCCESS("Seed OK (DFM + lignes)."))
