#!/usr/bin/env python
"""
Script pour simuler le paiement d'une demande de kit et la rendre testable.
Utilisation : python manage.py shell < simulate_payment.py
Ou copiez-collez le contenu dans : python manage.py shell
"""
import os
import sys
import django

# Setup Django (si lancé directement)
if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(__file__))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from store.models import ClientInquiry, InquiryDocument
from django.core.files.base import ContentFile

print("=" * 80)
print("🔧 SIMULATION DE PAIEMENT POUR TEST")
print("=" * 80)
print()

# Option 1 : Modifier une demande existante
print("Option 1 : Modifier une demande existante")
print("-" * 80)

existing_kits = ClientInquiry.objects.filter(kind='KIT').order_by('-created_at')[:5]

if existing_kits.exists():
    print(f"Demandes de kit trouvées : {existing_kits.count()}\n")
    
    for idx, kit in enumerate(existing_kits, 1):
        docs_count = InquiryDocument.objects.filter(inquiry=kit).count()
        print(f"  {idx}. Demande #{kit.pk}")
        print(f"     Client: {kit.contact_name or kit.email}")
        print(f"     Email: {kit.email}")
        print(f"     Payment status: {kit.payment_status}")
        print(f"     Processing state: {kit.processing_state}")
        print(f"     Documents: {docs_count}")
        print()
    
    # Modifier la première demande pour la rendre testable
    first_kit = existing_kits.first()
    
    print(f"🎯 Modification de la demande #{first_kit.pk} pour la rendre testable...")
    print()
    
    # Simuler le paiement
    first_kit.payment_status = 'PAID'
    first_kit.processing_state = 'PAID'
    first_kit.save(update_fields=['payment_status', 'processing_state'])
    
    print(f"✅ Demande #{first_kit.pk} mise à jour !")
    print(f"   payment_status: {first_kit.payment_status}")
    print(f"   processing_state: {first_kit.processing_state}")
    print()
    print("🌐 Accédez à : http://localhost:8000/kit-complet-traitement/")
    print(f"👉 La demande #{first_kit.pk} est maintenant testable !")
    print()
    
else:
    print("⚠️  Aucune demande de kit trouvée.")
    print()
    print("Option 2 : Créer une nouvelle demande de test")
    print("-" * 80)
    print()
    
    # Créer une demande de test complète
    inquiry = ClientInquiry.objects.create(
        kind="KIT",
        contact_name="Alice Martin",
        email="alice.martin@mairie-test.ml",
        organization_name="Mairie de Bamako Centre",
        statut_juridique="Collectivité territoriale",
        location="Bamako, Mali",
        sector="Administration publique",
        mission_text="Gestion des services municipaux : finances, urbanisme, état civil, affaires sociales",
        context_text="Administration publique de 80 agents avec un budget annuel de 200M FCFA. "
                     "Structure organisée en 5 services principaux.",
        notes_text="Demande d'un kit complet pour préparer l'audit annuel prévu dans 3 mois.",
        budget_range="100M-500M FCFA",
        funding_sources=["Taxes locales", "Subventions de l'État"],
        audits_types=["Financier", "Conformité", "Performance"],
        audits_frequency="Annuel",
        staff_size="50-100",
        selected_tier_code="complete_pro",
        payment_status="PAID",
        processing_state="PAID"
    )
    
    # Ajouter un document réaliste
    doc_content = """RÈGLEMENT INTÉRIEUR - MAIRIE DE BAMAKO CENTRE

TITRE I - ORGANISATION GÉNÉRALE

Article 1 - Structure administrative
La mairie est organisée en 5 services principaux :
- Service des finances et du budget (15 agents)
- Service de l'urbanisme et de l'habitat (20 agents)
- Service de l'état civil (10 agents)
- Service des affaires sociales et culturelles (15 agents)
- Service technique et logistique (20 agents)

Article 2 - Organes de direction
Le maire est assisté de :
- Un secrétaire général
- 5 chefs de service
- Un contrôleur financier

TITRE II - CONTRÔLE INTERNE ET AUDIT

Article 3 - Audit interne
Un audit interne est réalisé annuellement par le contrôleur municipal.
Le rapport d'audit est transmis au conseil municipal avant le 31 mars.

Article 4 - Audit externe
Un cabinet d'audit externe certifie les comptes tous les 2 ans.
Le dernier audit date de 2023.

Article 5 - Contrôle de gestion
Un tableau de bord mensuel est produit par le service finances.

TITRE III - GESTION FINANCIÈRE ET BUDGÉTAIRE

Article 6 - Documents comptables obligatoires
La mairie doit tenir à jour :
- Le registre des délibérations du conseil municipal (conservation 10 ans)
- Le livre journal des recettes et dépenses
- L'inventaire annuel du patrimoine communal
- Les registres d'état civil
- Les contrats et marchés publics (conservation 5 ans)

Article 7 - Procédures d'engagement
- Tout engagement de dépense >5000 FCFA nécessite un bon de commande
- Les paiements >50000 FCFA nécessitent une validation du maire
- Contrôle a priori sur toutes dépenses >100000 FCFA

Article 8 - Gestion de trésorerie
- Rapprochement bancaire mensuel obligatoire
- Visa du contrôleur financier sur tous les mandats
- Caisse limitée à 500000 FCFA

TITRE IV - MARCHÉS PUBLICS

Article 9 - Seuils de passation
- Marchés <10M FCFA : consultation simplifiée
- Marchés 10M-50M FCFA : appel d'offres restreint
- Marchés >50M FCFA : appel d'offres ouvert

Article 10 - Commission des marchés
Une commission examine tous les marchés >10M FCFA.
Composition : maire, secrétaire général, chef service finances, 2 conseillers.

TITRE V - RESSOURCES HUMAINES

Article 11 - Recrutement
Tout recrutement suit la procédure de la fonction publique territoriale.
Concours obligatoire pour les postes permanents.

Article 12 - Formation
Budget formation : 2% de la masse salariale annuelle.
Plan de formation validé par le conseil municipal.

TITRE VI - PATRIMOINE ET ÉQUIPEMENTS

Article 13 - Inventaire
Inventaire physique annuel de tous les biens meubles et immeubles.
Mise à jour du registre d'inventaire avant le 31 décembre.

Article 14 - Maintenance
Plan de maintenance préventive pour tous les équipements municipaux.
Contrôle technique annuel des véhicules de service.

TITRE VII - TRANSPARENCE ET INFORMATION

Article 15 - Publications
Les délibérations du conseil sont publiées sur le site web municipal.
Affichage obligatoire en mairie sous 15 jours.

Article 16 - Accès aux documents
Tout citoyen peut consulter les documents administratifs non confidentiels.
Registre des consultations tenu à jour.

FAIT À BAMAKO, LE 15 JANVIER 2024
LE MAIRE
[Signature]
"""
    
    doc = InquiryDocument.objects.create(
        inquiry=inquiry,
        original_name="reglement_interieur_mairie.txt"
    )
    doc.file.save("reglement_interieur.txt", ContentFile(doc_content.encode()))
    
    print("✅ NOUVELLE DEMANDE DE TEST CRÉÉE !")
    print("=" * 80)
    print(f"ID : {inquiry.pk}")
    print(f"Client : {inquiry.contact_name}")
    print(f"Email : {inquiry.email}")
    print(f"Organisation : {inquiry.organization_name}")
    print(f"Payment status : {inquiry.payment_status}")
    print(f"Processing state : {inquiry.processing_state}")
    print(f"Documents : 1 fichier (Règlement intérieur)")
    print()
    print("🌐 URL de test : http://localhost:8000/kit-complet-traitement/")
    print()
    print("👉 Cette demande est prête pour le traitement IA !")
    print("   Cliquez sur 'Traiter avec l'IA' pour lancer la génération.")
    print()

print("=" * 80)
print("✅ SIMULATION TERMINÉE")
print("=" * 80)
print()
print("📝 Notes :")
print("  - La demande est maintenant dans l'état PAID")
print("  - Le bouton 'Traiter avec l'IA' devrait être visible")
print("  - Vous pouvez lancer le traitement immédiatement")
print()
print("🚀 Prochaine étape :")
print("  1. Allez sur http://localhost:8000/kit-complet-traitement/")
print("  2. Cliquez sur 'Traiter avec l'IA'")
print("  3. Attendez 30-60 secondes")
print("  4. Téléchargez le brouillon généré !")
print()

