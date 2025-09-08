# store/seeds/ebook_irregularities.py

SEED_IRREGULARITIES = {
    # clé = slug du produit
    "audit-services-publics": [
        {
            "irregularite": "Passation de marchés non conforme (fractionnement, absence d’AO, absence de no-objection)",
            "reference": (
                "Accord de financement & Lettre de décaissement (DFIL) du bailleur ; "
                "Manuel de procédures du projet ; Code/Directive des marchés publics ; "
                "Règlement de passation des marchés du bailleur (ex. Banque mondiale) ; Dossiers d’AO & STEP."
            ),
            "acteurs": (
                "Unité de gestion du projet (UGP), cellule de passation des marchés (CPM), "
                "coordonnateur, contrôleur financier, bailleur (spécialiste en passation)."
            ),
            "dispositions": (
                "Plan de passation validé & publié ; utilisation de STEP ; "
                "vérifier seuils & méthodes ; obtenir les no-objection écrits ; "
                "séparation des tâches (rédaction/évaluation/approbation) ; "
                "tenue d’un dossier d’achat complet (TDR, critères, PV, rapports d’évaluation)."
            ),
        },
        {
            "irregularite": "Dépenses inéligibles / non justifiées (hors catégorie, TVA non éligible, pièces absentes)",
            "reference": (
                "Accord de financement & DFIL (catégories/conditions d’éligibilité) ; "
                "Manuel de gestion financière ; instructions IFR ; états de rapprochement ; "
                "politique fiscale applicable."
            ),
            "acteurs": (
                "RAF/DAF, comptable projet, ordonnateur, agence fiduciaire/banque, "
                "auditeur externe, spécialiste en gestion financière du bailleur."
            ),
            "dispositions": (
                "Checklist d’éligibilité avant paiement ; pièces justificatives complètes (contrat, facture, PV, preuve service fait) ; "
                "contrôle à 2 niveaux (initiation/approbation) ; suivi des avances & apurement ; "
                "IFR trimestriels concordants avec catégories ; corrections/rejets documentés."
            ),
        },
        {
            "irregularite": "Gestion du Compte désigné/avances défaillante (justifications tardives, écarts non rapprochés)",
            "reference": (
                "Lettre de décaissement (DFIL) & directives de décaissement ; "
                "Procédures de trésorerie du projet ; relevés bancaires & rapprochements ; "
                "journal des décaissements & IFR."
            ),
            "acteurs": (
                "Comptable projet, RAF/DAF, ordonnateur, banque commerciale, "
                "spécialiste décaissements du bailleur, auditeur externe."
            ),
            "dispositions": (
                "Calendrier d’apurement des avances (ex. sous 30 jours) ; "
                "rapprochement bancaire mensuel signé ; contrôles de seuils & pièces avant décaissement ; "
                "double signature & piste d’audit ; suivi des écritures en suspens & apurement documenté."
            ),
        },
    ]
}
