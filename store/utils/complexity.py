"""
Calcul automatique de la complexité des dossiers.
"""
import re
from typing import List


def calculate_complexity_score(
    context_text: str = "",
    audits_types: List[str] = None,
    funding_sources: List[str] = None,
    sector: str = "",
    staff_size: str = "",
    notes_text: str = "",
    docs_count: int = 1,
) -> str:
    """
    Calcule automatiquement la complexité des dossiers basée sur plusieurs indicateurs.
    
    Retourne: "simple", "standard", ou "complexe"
    
    Facteurs de complexité:
    - Nombre de documents (plus = plus complexe)
    - Types d'audits (Cour des comptes, enquêtes = plus complexe)
    - Mots-clés dans le contexte (sensible, fraud, irrégularité, etc.)
    - Secteur d'activité (public, santé, finances = plus complexe)
    - Taille de l'organisation (plus grande = potentiellement plus complexe)
    """
    if audits_types is None:
        audits_types = []
    if funding_sources is None:
        funding_sources = []
    
    score = 0
    all_text = f"{context_text} {notes_text}".lower()
    
    # 1. Types d'audits complexes
    complex_audit_keywords = [
        "externe_courdescomptes",  # Cour des comptes
        "fraude_enquete",  # Enquêtes
        "financier",  # Audit financier
        "passation_marches",  # Marchés publics
    ]
    for audit_type in audits_types:
        if audit_type in complex_audit_keywords:
            score += 3
    
    # 2. Mots-clés de complexité dans le texte
    complexity_keywords = [
        "sensible", "sensibles", "sensitive",
        "fraude", "fraud", "irrégularité", "irrégularités",
        "litige", "litiges", "conflit", "conflits",
        "urgence", "urgent", "échéance", "échéances",
        "complexe", "compliqué", "difficile",
        "sanction", "sanctions", "amende", "amendes",
        "contrôle", "inspection", "investigation",
        "risque", "risques", "menace", "menaces",
    ]
    for keyword in complexity_keywords:
        count = all_text.count(keyword)
        score += count * 2
    
    # 3. Secteurs complexes
    complex_sectors = [
        "santé", "health", "médical", "hospitalier",
        "finance", "financier", "bancaire", "bank",
        "public", "état", "gouvernement", "government",
        "éducation", "education", "école", "université",
    ]
    sector_lower = sector.lower()
    for cs in complex_sectors:
        if cs in sector_lower:
            score += 2
            break
    
    # 4. Taille de l'organisation (plus grande = plus complexe potentiellement)
    if staff_size:
        # Extraire les nombres du texte
        numbers = re.findall(r'\d+', staff_size)
        if numbers:
            try:
                size = int(numbers[0])
                if size > 100:
                    score += 2
                elif size > 50:
                    score += 1
            except (ValueError, IndexError):
                pass
    
    # 5. Nombre de documents (plus = potentiellement plus complexe)
    if docs_count > 7:
        score += 3
    elif docs_count > 4:
        score += 2
    elif docs_count > 2:
        score += 1
    
    # 6. Sources de financement (certaines sont plus complexes)
    complex_funding = [
        "appuis_ptf",  # Projets PTF peuvent être complexes
        "fonds_speciaux",  # Fonds spéciaux
    ]
    for fs in funding_sources:
        if fs in complex_funding:
            score += 1
    
    # 7. Longueur du contexte (plus de détails = peut indiquer plus de complexité)
    if len(context_text) > 1000:
        score += 2
    elif len(context_text) > 500:
        score += 1
    
    # Déterminer le niveau final
    if score >= 10:
        return "complexe"
    elif score >= 5:
        return "standard"
    else:
        return "simple"

