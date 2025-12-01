"""
Calcul du prix estimé pour les kits basé sur les tarifs de référence.
"""
import re
from typing import Dict, Tuple


def determine_tier_by_docs_count(docs_count: int) -> str:
    """
    Détermine le tier approprié selon le nombre de documents.
    
    Retourne: "essentiel_plus", "complete_pro", "expert_audit", ou "sur_mesure"
    """
    if docs_count <= 3:
        return "essentiel_plus"
    elif docs_count <= 6:
        return "complete_pro"
    elif docs_count <= 10:
        return "expert_audit"
    else:
        return "sur_mesure"


def parse_price_range(price_range_str: str) -> Tuple[int, int]:
    """
    Parse une chaîne de fourchette de prix comme "45 000 – 65 000" 
    en tuple (min, max).
    
    Retourne: (min_price, max_price) en FCFA
    """
    if not price_range_str:
        return (45000, 65000)  # Default
    
    # Nettoyer la chaîne
    price_range_str = price_range_str.replace("–", "-").replace("—", "-")
    price_range_str = price_range_str.replace(",", "").replace(" ", "")
    
    # Extraire les nombres
    numbers = re.findall(r'\d+', price_range_str)
    if len(numbers) >= 2:
        try:
            min_price = int(numbers[0])
            max_price = int(numbers[1])
            return (min_price, max_price)
        except (ValueError, IndexError):
            pass
    
    # Si un seul nombre, créer une fourchette autour
    if len(numbers) == 1:
        try:
            base = int(numbers[0])
            return (int(base * 0.8), int(base * 1.2))
        except ValueError:
            pass
    
    return (45000, 65000)  # Default fallback


def calculate_estimated_price(
    docs_count: int,
    complexity: str,
    price_range_str: str,
) -> Dict[str, int]:
    """
    Calcule le prix estimé en fonction du nombre de documents et de la complexité.
    
    Args:
        docs_count: Nombre de documents
        complexity: "simple", "standard", ou "complexe"
        price_range_str: Fourchette tarifaire du tier (ex: "45 000 – 65 000")
    
    Retourne:
        Dict avec 'min_price', 'max_price', 'suggested_price' (FCFA)
    """
    min_price, max_price = parse_price_range(price_range_str)
    
    # Ajuster selon la complexité
    # Simple: -10% du min, standard: milieu, complexe: +10% du max
    if complexity == "simple":
        suggested_price = int(min_price * 0.9)
    elif complexity == "complexe":
        suggested_price = int(max_price * 1.1)
    else:  # standard
        suggested_price = int((min_price + max_price) / 2)
    
    # Ajuster légèrement selon le nombre de documents dans le tier
    tier = determine_tier_by_docs_count(docs_count)
    
    if tier == "essentiel_plus":
        # Plus de documents = plus proche du max
        if docs_count == 3:
            suggested_price = int(suggested_price * 1.15)
        elif docs_count == 2:
            suggested_price = int(suggested_price * 1.05)
    elif tier == "complete_pro":
        # Plus de documents = plus proche du max
        if docs_count == 6:
            suggested_price = int(suggested_price * 1.1)
        elif docs_count == 4:
            suggested_price = int(suggested_price * 0.95)
    elif tier == "expert_audit":
        # Plus de documents = plus proche du max
        if docs_count >= 9:
            suggested_price = int(suggested_price * 1.1)
        elif docs_count == 7:
            suggested_price = int(suggested_price * 0.95)
    
    # S'assurer que le prix suggéré reste dans une fourchette raisonnable
    suggested_price = max(min_price, min(suggested_price, int(max_price * 1.15)))
    
    return {
        "min_price": min_price,
        "max_price": max_price,
        "suggested_price": suggested_price,
    }

