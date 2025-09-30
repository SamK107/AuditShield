from django.core.management.base import BaseCommand

from store.models import PreliminaryRow, PreliminaryTable, Product


class Command(BaseCommand):
    help = "Seed d'une table d'analyse préliminaire (DFM) avec 3 lignes d'exemple"

    def handle(self, *args, **options):
        product = Product.objects.filter(is_published=True).first()
        if not product:
            product, _ = Product.objects.get_or_create(
                slug="audit-services-publics",
                defaults=dict(
                    title="Ebook - Audit Sans Peur",
                    subtitle="",
                    price_fcfa=15000,
                    is_published=True,
                ),
            )

        table, _ = PreliminaryTable.objects.get_or_create(
            product=product,
            slug="dfm",
            defaults=dict(
                title="Direction des finances et du matériel (DFM)",
                group=PreliminaryTable.STRUCTURE,
                order=0,
                description="Extrait de l'analyse préliminaire issue de l'ebook.",
            ),
        )

        rows = [
            dict(
                order=0,
                irregularity="Rapprochements bancaires non réalisés",
                reference="SYSCOHADA 2017, PCG § Trésorerie",
                actors="DFM, comptable",
                dispositions="Vérifier chaque mois ; faire signer DFM et ordonnateur.",
            ),
            dict(
                order=10,
                irregularity="Dépenses hors crédits disponibles",
                reference="Loi de finances nationale",
                actors="Ordonnateur, contrôleur financier",
                dispositions="Contrôle des engagements avant ordonnancement.",
            ),
            dict(
                order=20,
                irregularity="Justificatifs incomplets (factures sans PV)",
                reference="Décret marchés publics",
                actors="DFM, service marchés",
                dispositions="Dossier complet = contrat + PV + facture.",
            ),
        ]
        created = 0
        for r in rows:
            _, was_created = PreliminaryRow.objects.get_or_create(
                table=table,
                irregularity=r["irregularity"],
                defaults=r,
            )
            created += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(f"OK — table '{table.title}' prête, lignes créées: {created}")
        )
