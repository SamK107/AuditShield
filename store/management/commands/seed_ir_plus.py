# store/management/commands/seed_ir_plus.py
from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import IrregularityCategory, IrregularityRow, Product

DATA_PLUS = {
    # 1) DFM
    "dfm": {
        "title": "Direction des finances et du matériel (DFM)",
        "group": "STRUCTURE",
        "order": 0,
        "rows": [
            dict(
                irregularity="Rapprochements bancaires non réalisés ou non signés",
                reference="SYSCOHADA 2017 – PCG (Trésorerie); Manuel de trésorerie interne",
                actors="DFM, Comptable, Ordonnateur",
                dispositions=(
                    "Établir un calendrier mensuel de rapprochement (J+5) ;\n"
                    "Utiliser un modèle normalisé (pièce jointe au dossier de clôture) ;\n"
                    "Faire signer DFM + Ordonnateur ;\n"
                    "Traiter et justifier les écarts sous 7 jours ;\n"
                    "Archiver: relevés, rapprochement, pièces justificatives bancaires."
                ),
            ),
            dict(
                irregularity="Engagements/ordonnancements sans crédits disponibles",
                reference="LOLF/Directives UEMOA Finances publiques; Loi de finances; Circulaires budgétaires",
                actors="Ordonnateur, Contrôleur financier, DFM",
                dispositions=(
                    "Mettre en place un registre des engagements (SEB) tenu à jour ;\n"
                    "Exiger le visa du Contrôle financier avant tout engagement ;\n"
                    "Refuser l’ordonnancement hors crédits ;\n"
                    "Mettre en place un suivi des AE/CP avec alertes de seuils."
                ),
            ),
            dict(
                irregularity="Dossiers de dépense incomplets (contrat/PV/facture absents ou non conformes)",
                reference="Code des marchés publics (procédures, seuils, pièces); Instructions de comptabilité publique",
                actors="Service Marchés, DFM, CMP",
                dispositions=(
                    "Imposer une check-list dossier complet : décision/contrat ou BC + PV réception + facture + pièces fiscales ;\n"
                    "Vérifier concordance des montants/dates ;\n"
                    "Rejeter toute pièce non signée ou antidatée ;\n"
                    "Archiver par exercice et par marché."
                ),
            ),
            dict(
                irregularity="Régies d’avances non apurées dans les délais",
                reference="Textes nationaux sur régies d’avances/recettes; Instructions du Trésor",
                actors="Régisseur, DFM, Ordonnateur, Trésorier",
                dispositions=(
                    "Fixer une périodicité d’apurement (au moins mensuelle) ;\n"
                    "Exiger pièces probantes et états de régie ;\n"
                    "Interdire les décaissements hors objet de la régie ;\n"
                    "PV de remise/reprise de fonds en cas de changement de régisseur."
                ),
            ),
            dict(
                irregularity="Service fait non établi avant paiement (PV de réception absent ou non conforme)",
                reference="Code des marchés publics; Manuels internes de réception",
                actors="Service technique, Service Marchés, DFM",
                dispositions=(
                    "Réaliser une réception contradictoire (PV signé) ;\n"
                    "Joindre rapports/attachements, photos si nécessaire ;\n"
                    "Bloquer tout paiement sans preuve de service fait ;\n"
                    "Enregistrer les non-conformités et actions correctives."
                ),
            ),
        ],
    },
    # 2) Collectivités
    "collectivites": {
        "title": "Collectivités territoriales",
        "group": "STRUCTURE",
        "order": 10,
        "rows": [
            dict(
                irregularity="Budget non adopté/délibéré dans les délais réglementaires",
                reference="Code des collectivités territoriales; Calendrier budgétaire annuel",
                actors="Élus (Conseil), Maire/Président, DAF",
                dispositions=(
                    "Élaborer le calendrier budgétaire et l’ordre du jour des sessions ;\n"
                    "Tenir la séance de vote et établir la délibération ;\n"
                    "Transmettre à la tutelle dans les délais ;\n"
                    "Publier et afficher les documents budgétaires."
                ),
            ),
            dict(
                irregularity="Plan de passation des marchés (PPM) absent ou non publié",
                reference="Réglementation des marchés publics; Guides nationaux PPM",
                actors="DAF, Service Marchés, CMP",
                dispositions=(
                    "Élaborer/mettre à jour le PPM en cohérence avec le budget ;\n"
                    "Valider et publier le PPM (site officiel/BO) ;\n"
                    "Suivre l’exécution et réviser en cas de besoins imprévus ;\n"
                    "Conserver les preuves de publication."
                ),
            ),
            dict(
                irregularity="Régies d’avances/recettes non justifiées ou au-delà des plafonds",
                reference="Textes régies d’avances/recettes; Instructions du Trésor",
                actors="Régisseur, Ordonnateur, Trésor",
                dispositions=(
                    "Définir les plafonds et objets de régie ;\n"
                    "Reddition mensuelle avec pièces ;\n"
                    "Dépôts réguliers à la banque/Trésor ;\n"
                    "Contrôles inopinés et PV de caisse."
                ),
            ),
            dict(
                irregularity="Inventaire du patrimoine non réalisé ou non rapproché à la comptabilité",
                reference="Réglementation comptabilité matières; SYSCOHADA – stocks/immobilisations",
                actors="Patrimoine, DAF, Contrôle interne",
                dispositions=(
                    "Réaliser l’inventaire physique annuel ;\n"
                    "Mettre à jour fiches de biens et étiquetage ;\n"
                    "Rapprocher inventaire/comptabilité et justifier les écarts ;\n"
                    "Rapport d’inventaire signé et plan d’action."
                ),
            ),
            dict(
                irregularity="Recettes locales non titrées/non recouvrées (quittanciers et états absents)",
                reference="Textes nationaux de recouvrement et régies de recettes",
                actors="Percepteur/Trésor, Service Recettes, DAF",
                dispositions=(
                    "Émettre les titres de recettes ;\n"
                    "Délivrer des quittances numérotées ;\n"
                    "Rapprocher quotidiennement régie/Trésor ;\n"
                    "Suivre les arriérés et engager les poursuites prévues."
                ),
            ),
        ],
    },
    # 3) EPIC
    "epic": {
        "title": "EPIC",
        "group": "STRUCTURE",
        "order": 20,
        "rows": [
            dict(
                irregularity="Facturation sans service fait (contrat/BL/PV manquants)",
                reference="Procédures internes de vente/prestation; SYSCOHADA – principes de comptabilisation",
                actors="Exploitation, Contrôle de gestion, DAF",
                dispositions=(
                    "Exiger BL ou PV signé avant toute facture ;\n"
                    "Mettre en place un contrôle croisé exploitation/DAF ;\n"
                    "Bloquer la validation comptable sans preuve ;\n"
                    "Suivi des litiges et avoirs avec justification."
                ),
            ),
            dict(
                irregularity="Dépassement de plafond de caisse et régularisation tardive",
                reference="Manuel de trésorerie interne; Instructions de caisse",
                actors="Caissier, DAF, Contrôle interne",
                dispositions=(
                    "Fixer un plafond de caisse et journal de caisse quotidien ;\n"
                    "Dépôt bancaire régulier (J+1) ;\n"
                    "Contrôles inopinés documentés ;\n"
                    "Écarts justifiés et approuvés par PV."
                ),
            ),
            dict(
                irregularity="Stocks sans inventaires périodiques et écarts non traités",
                reference="SYSCOHADA – stocks; Procédures magasin",
                actors="Magasinier, Contrôle interne, DAF",
                dispositions=(
                    "Inventaires mensuels/trimestriels planifiés ;\n"
                    "Analyse des écarts et actions correctives ;\n"
                    "Séparation des tâches commandes/réception/stock ;\n"
                    "Traçabilité des sorties (bons signés)."
                ),
            ),
            dict(
                irregularity="Contrats sans revue juridique ni délégations de signature traçables",
                reference="Procédures contractuelles internes; Délégation de signature",
                actors="Juridique, DG, DAF",
                dispositions=(
                    "Mettre en place une revue juridique préalable ;\n"
                    "Formaliser les délégations (acte + registre) ;\n"
                    "Contrôler les échéances et avenants ;\n"
                    "Archivage central des originaux signés."
                ),
            ),
            dict(
                irregularity="Conflits d’intérêts non déclarés dans les achats",
                reference="Code de conduite; Politique anticorruption (normes IIA/COSO)",
                actors="Achats, CMP, Tous agents",
                dispositions=(
                    "Déployer un formulaire annuel de déclaration d’intérêts ;\n"
                    "Tenir un registre et actualiser avant chaque comité ;\n"
                    "Exclure l’agent concerné de l’évaluation ;\n"
                    "Sanctionner toute fausse déclaration."
                ),
            ),
        ],
    },
    # 4) ONG
    "ong": {
        "title": "ONG",
        "group": "STRUCTURE",
        "order": 30,
        "rows": [
            dict(
                irregularity="Dépenses hors budget approuvé ou non éligibles",
                reference="PRAG UE 2021 / Guides bailleurs; Accords de financement et annexes",
                actors="Coordonnateur, RAF, Comptable",
                dispositions=(
                    "Tracer toute variation budgétaire (virement) avec approbation ;\n"
                    "Vérifier l’éligibilité selon le bailleur ;\n"
                    "Documenter les non-éligibilités et réaffectations ;\n"
                    "Mettre à jour le suivi budgétaire mensuel."
                ),
            ),
            dict(
                irregularity="Dossiers de dépense non conformes aux exigences bailleur",
                reference="Guides bailleurs (UE/AFD/BM); Manuel de procédures ONG",
                actors="RAF, Achats, Comptable",
                dispositions=(
                    "Utiliser une check-list bailleur spécifique ;\n"
                    "Exiger listes de présence signées, attestations, PV ;\n"
                    "Contrôle croisé avant paiement ;\n"
                    "Archivage numérique + papier."
                ),
            ),
            dict(
                irregularity="Paiements en espèces au-delà des seuils autorisés",
                reference="Politiques bailleurs – anti-fraude; Manuel financier ONG",
                actors="RAF, Caissier, Comptable",
                dispositions=(
                    "Imposer le virement bancaire au-delà du seuil ;\n"
                    "Justifier toute exception par note approuvée ;\n"
                    "Concilier caisse quotidiennement ;\n"
                    "Contrôles inopinés et PV."
                ),
            ),
            dict(
                irregularity="Feuilles de temps (timesheets) absentes ou non signées",
                reference="Exigences bailleurs RH; Manuel RH ONG",
                actors="RH, Chefs de projet, Personnel",
                dispositions=(
                    "Timesheets mensuels signés employé + supérieur ;\n"
                    "Concordance avec contrats et fiches de paie ;\n"
                    "Archivage et contrôle trimestriel ;\n"
                    "Rejet des charges sans timesheet conforme."
                ),
            ),
            dict(
                irregularity="Procédures d’achats sans mise en concurrence (devis) ni justification",
                reference="PRAG UE/Manuels bailleurs – seuils & procédures",
                actors="Achats, RAF, CMP",
                dispositions=(
                    "Exiger min. 3 devis ou justification formelle ;\n"
                    "Rapport d’évaluation signé ;\n"
                    "Publication interne des attributions ;\n"
                    "Registre des dérogations approuvées."
                ),
            ),
        ],
    },
    # 5) Projet BM
    "projet-bm": {
        "title": "Projet de développement (Banque mondiale)",
        "group": "STRUCTURE",
        "order": 40,
        "rows": [
            dict(
                irregularity="Non-conformité aux Procurement Regulations (IPF Borrowers)",
                reference="World Bank Procurement Regulations (July 2016, rev. Nov 2020); Dossiers types",
                actors="Spécialiste Passation, UGP/UCP, Coordonnateur",
                dispositions=(
                    "Planifier dans STEP et utiliser les Dossiers types ;\n"
                    "Définir des critères d’évaluation clairs et mesurables ;\n"
                    "Rapport d’évaluation conforme, approuvé ;\n"
                    "Archivage complet dans STEP/dossier physique."
                ),
            ),
            dict(
                irregularity="Absence de No Objection (NO) aux étapes obligatoires",
                reference="Procédures BM – revue préalable; Conditions du Financement",
                actors="UGP/UCP, Coordonnateur, Passation",
                dispositions=(
                    "Établir un plan de points NO (plan de revue) ;\n"
                    "Soumettre via STEP et conserver les NO ;\n"
                    "Bloquer l’étape suivante sans NO ;\n"
                    "Journal des correspondances avec la BM."
                ),
            ),
            dict(
                irregularity="IFR tardifs ou incohérents",
                reference="Disbursement & Financial Information Letter (DFIL); Manuel de gestion financière du projet",
                actors="Spécialiste financier, Comptable projet",
                dispositions=(
                    "Calendrier IFR trimestriel ;\n"
                    "Rapprochement banques/comptabilité avant émission ;\n"
                    "Revue interne (4 yeux) et check-list ;\n"
                    "Dépôt dans les délais avec accusé de réception."
                ),
            ),
            dict(
                irregularity="Dépenses inéligibles selon l’Accord de financement",
                reference="Financing Agreement; Anti-Corruption Guidelines (July 2016)",
                actors="UGP, Spécialiste financier, Audit interne",
                dispositions=(
                    "Vérifier l’éligibilité avant engagement ;\n"
                    "Mettre à jour la liste d’exclusions ;\n"
                    "Procédure de remboursement/reclassement documentée ;\n"
                    "Report à l’audit interne et au comité de pilotage."
                ),
            ),
            dict(
                irregularity="Suivi environnemental & social insuffisant (ESF) et GRM absent",
                reference="Environmental & Social Framework (ESF 2018); Plans d’action E&S; GRM",
                actors="Spécialiste E&S, UGP, Supervision",
                dispositions=(
                    "Mettre à jour les plans E&S (ESMP/ESCP) ;\n"
                    "Opérationnaliser le GRM (registre, délais de réponse) ;\n"
                    "Rapports trimestriels E&S avec indicateurs ;\n"
                    "Tracer les incidents et actions correctives."
                ),
            ),
        ],
    },
}


class Command(BaseCommand):
    help = "Seed des lignes Version PLUS (5 irrégularités par catégorie : DFM, Collectivités, EPIC, ONG, Projet BM)."

    @transaction.atomic
    def handle(self, *args, **options):
        product = Product.objects.filter(is_published=True).first()
        if not product:
            product, _ = Product.objects.get_or_create(
                slug="audit-sans-peur",
                defaults=dict(
                    title="Ebook - Audit Sans Peur",
                    subtitle="Le guide concret pour éviter les mauvaises surprises.",
                    price_fcfa=15000,
                    is_published=True,
                ),
            )
            self.stdout.write(
                self.style.WARNING("Aucun produit publié trouvé — produit par défaut créé.")
            )

        total_cats, total_rows, created_rows = 0, 0, 0

        for slug, meta in DATA_PLUS.items():
            cat, cat_created = IrregularityCategory.objects.get_or_create(
                product=product,
                slug=slug,
                defaults=dict(
                    title=meta["title"],
                    group=meta["group"],
                    order=meta["order"],
                    description=meta.get("description", ""),
                ),
            )
            total_cats += 1

            # Insère 5 lignes Version PLUS par catégorie
            for idx, row in enumerate(meta["rows"]):
                total_rows += 1
                obj, was_created = IrregularityRow.objects.get_or_create(
                    category=cat,
                    version="PLUS",
                    irregularity=row["irregularity"],  # clé simple pour éviter doublons
                    defaults=dict(
                        order=idx * 10,  # 0,10,20,30,40
                        product=product,  # si ton modèle a ce champ
                        reference=row["reference"],
                        actors=row["actors"],
                        dispositions=row["dispositions"],
                    ),
                )
                created_rows += int(was_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"OK — catégories traitées: {total_cats}; lignes PLUS demandées: {total_rows}; créées: {created_rows}"
            )
        )
