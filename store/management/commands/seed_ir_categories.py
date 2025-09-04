# store/management/commands/seed_ir_categories.py
from django.core.management.base import BaseCommand
from django.db import transaction
from store.models import (
    Product, IrregularityCategory, IrregularityRow,
)

CATS = [
    {
        "title": "Direction des finances et du matériel (DFM)",
        "slug": "dfm",
        "group": "STRUCTURE",
        "order": 0,
        "rows_ebook": [
            dict(irregularity="Rapprochements bancaires non réalisés",
                 reference="SYSCOHADA 2017 – PCG (Trésorerie)",
                 actors="DFM, Comptable",
                 dispositions="Rapprochement mensuel; justification des écarts; signatures DFM + Ordonnateur."),
            dict(irregularity="Dépenses hors crédits disponibles",
                 reference="Loi de finances; régulation budgétaire",
                 actors="Ordonnateur, Contrôleur financier, DFM",
                 dispositions="Contrôle des engagements; visa CF préalable; suivi des crédits."),
            dict(irregularity="Justificatifs incomplets (factures sans PV)",
                 reference="Décret marchés publics; manuels internes",
                 actors="DFM, Service marchés",
                 dispositions="Dossier complet: contrat/BC + PV réception + facture; numérotation; archivage."),
            dict(irregularity="Fractionnement de marchés",
                 reference="Code/Directives UEMOA – seuils",
                 actors="CMP, DFM, Ordonnateur",
                 dispositions="Consolider les besoins au PPM; respect des seuils; traçabilité des demandes."),
            dict(irregularity="Retard de liquidation des missions",
                 reference="Textes nationaux – missions/déplacements",
                 actors="DAF/DFM, Ordonnateur",
                 dispositions="Ordres de mission signés; Etats liquidatifs sous 15j; pièces justificatives complètes."),
        ],
    },
    {
        "title": "Collectivités territoriales",
        "slug": "collectivites",
        "group": "STRUCTURE",
        "order": 10,
        "rows_ebook": [
            dict(irregularity="Budget non adopté dans les délais",
                 reference="Code des collectivités; calendrier budgétaire",
                 actors="Maire/Président, DAF, Conseil",
                 dispositions="Respect du calendrier; publicité; visas nécessaires."),
            dict(irregularity="Absence de plan de passation (PPM)",
                 reference="Réglementation marchés publics",
                 actors="DAF, Service marchés",
                 dispositions="Elaborer/mettre à jour le PPM; cohérence budget; publication."),
            dict(irregularity="Régies d’avances non justifiées",
                 reference="Textes sur régies d’avances/recettes",
                 actors="Régisseur, Ordonnateur, Trésor",
                 dispositions="Périodicité de reddition; pièces probantes; plafonds respectés."),
            dict(irregularity="Inventaire du patrimoine non réalisé",
                 reference="Normes secteur public; instructions patrimoine",
                 actors="DAF, Patrimoine",
                 dispositions="Inventaire annuel; fiches de biens; rapprochement comptable."),
            dict(irregularity="Non-respect des procédures de commande publique",
                 reference="Décret marchés publics",
                 actors="Service marchés, DAF, Ordonnateur",
                 dispositions="Choix de la procédure adapté; publicité; procès-verbaux conformes."),
        ],
    },
    {
        "title": "EPIC",
        "slug": "epic",
        "group": "STRUCTURE",
        "order": 20,
        "rows_ebook": [
            dict(irregularity="Facturation sans service fait",
                 reference="Procédures internes; principes comptables",
                 actors="Exploitation, Contrôle de gestion, DAF",
                 dispositions="PV de service fait; validation croisée; contrôle qualité."),
            dict(irregularity="Caisse non régularisée",
                 reference="Manuel de trésorerie; règles de caisse",
                 actors="Caissier, DAF",
                 dispositions="Plafonds de caisse; dépôts quotidiens; contrôle inopiné."),
            dict(irregularity="Stocks sans inventaire physique",
                 reference="Procédures stocks/magasin",
                 actors="Magasinier, Contrôle interne",
                 dispositions="Inventaire mensuel; écarts justifiés; séparation des tâches."),
            dict(irregularity="Contrats sans validation juridique",
                 reference="Procédures contractuelles",
                 actors="Juridique, DAF, Direction",
                 dispositions="Revue juridique préalable; délégation de signature; suivi échéances."),
            dict(irregularity="Absence de délégation de signature traçable",
                 reference="Gouvernance interne",
                 actors="Direction générale, DAF",
                 dispositions="Actes de délégation formalisés; registre; diffusion interne."),
        ],
    },
    {
        "title": "ONG",
        "slug": "ong",
        "group": "STRUCTURE",
        "order": 30,
        "rows_ebook": [
            dict(irregularity="Dépenses hors budget projet",
                 reference="Accords de financement; budget approuvé",
                 actors="Coordonnateur, RAF, Comptable",
                 dispositions="Variations validées; journal des virements; justification bailleur."),
            dict(irregularity="Pièces non conformes aux exigences bailleur",
                 reference="Manuels bailleurs (BM/UE/AFD)",
                 actors="RAF, Achats, Comptable",
                 dispositions="Check-list bailleur; contrôles de conformité; archivage numérique."),
            dict(irregularity="Paiements en espèces au-delà des seuils",
                 reference="Politiques bailleurs; anti-fraude",
                 actors="RAF, Caissier",
                 dispositions="Plafonds stricts; paiements bancaires; justification des exceptions."),
            dict(irregularity="Absence de timesheets signés",
                 reference="Règles RH bailleur; manuel RH",
                 actors="RH, Chefs de projet",
                 dispositions="Timesheets mensuels signés; validation hiérarchique; archivage."),
            dict(irregularity="Conflits d’intérêts non déclarés",
                 reference="Code de conduite; anticorruption",
                 actors="Tout personnel, Achats",
                 dispositions="Formulaire de déclaration; registre; exclusion des évaluations."),
        ],
    },
    {
        "title": "Projet de développement (Banque mondiale)",
        "slug": "projet-bm",
        "group": "STRUCTURE",
        "order": 40,
        "rows_ebook": [
            dict(irregularity="Non-conformité aux Procurement Regulations",
                 reference="World Bank Procurement Regulations",
                 actors="Spéc. passation, UGP/UCP",
                 dispositions="Dossier conforme; critères clairs; publication & NO Objection."),
            dict(irregularity="Absence de NO Objection sur étapes clés",
                 reference="Procédures BM (revue préalable)",
                 actors="UGP, Coordonnateur, Passation",
                 dispositions="Plan de revue préalable; calendrier; correspondances tracées."),
            dict(irregularity="Retard ou incohérence des IFR",
                 reference="Disbursement & Financial Information Letter",
                 actors="Spéc. financier, Comptable projet",
                 dispositions="Calendrier IFR; rapprochements bancaires; revues internes."),
            dict(irregularity="Dépenses inéligibles",
                 reference="Contrat de financement; listes d’exclusion",
                 actors="UGP, DAF",
                 dispositions="Revue d’éligibilité; séparation des tâches; journal d’ajustements."),
            dict(irregularity="Suivi E&S/GRM insuffisant",
                 reference="ESF – Environmental & Social Framework",
                 actors="Spéc. E&S, UGP",
                 dispositions="Plan d’action E&S; registre GRM; rapports trimestriels."),
        ],
    },
]

class Command(BaseCommand):
    help = "Crée 5 catégories (DFM, Collectivités, EPIC, ONG, Projet BM) + lignes EBOOK"

    @transaction.atomic
    def handle(self, *args, **options):
        product = Product.objects.filter(is_published=True).first()
        if not product:
            product, _ = Product.objects.get_or_create(
                slug="audit-services-publics",
                defaults=dict(
                    title="Audit des services publics",
                    subtitle="Le guide concret pour éviter les mauvaises surprises.",
                    price_fcfa=15000,
                    is_published=True,
                ),
            )
            self.stdout.write(self.style.WARNING("Aucun produit publié trouvé — produit par défaut créé."))

        created_c, created_r = 0, 0
        for c in CATS:
            cat, was_created = IrregularityCategory.objects.get_or_create(
                product=product, slug=c["slug"],
                defaults=dict(
                    title=c["title"],
                    group=c["group"],
                    order=c["order"],
                    description=c.get("description", ""),
                ),
            )
            created_c += int(was_created)

            for idx, row in enumerate(c["rows_ebook"]):
                _, row_created = IrregularityRow.objects.get_or_create(
                    category=cat,
                    version="EBOOK",
                    order=idx * 10,  # 0,10,20…
                    defaults={
                        "product": product,  # si champ présent
                        **row,
                    },
                )
                created_r += int(row_created)

        self.stdout.write(self.style.SUCCESS(
            f"OK — catégories créées: {created_c}, lignes EBOOK créées: {created_r}"
        ))
