"""
Module pour la construction du prompt et l'appel à l'API OpenAI
pour générer le contenu Markdown du kit complet.
"""
import logging
from typing import Tuple, Dict, Any

from django.conf import settings
from openai import OpenAI
from openai import APIError as OpenAIAPIError

logger = logging.getLogger(__name__)


class KitGenerationError(Exception):
    """Exception personnalisée pour les erreurs de génération de kit."""
    
    def __init__(self, message: str, error_code: str = None, error_details: dict = None):
        self.message = message
        self.error_code = error_code
        self.error_details = error_details
        super().__init__(self.message)


def build_kit_markdown(
    consignes_md: str,
    inquiry,
    documents_payload: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Construit le prompt et appelle l'API OpenAI pour générer le contenu Markdown du kit.

    Args:
        consignes_md: Texte Markdown des consignes métier pour la génération du kit
        inquiry: Instance de store.models.ClientInquiry
        documents_payload: Texte déjà préformaté contenant les extraits des documents joints

    Returns:
        Tuple de (markdown, usage_dict):
          - markdown: contenu du kit en Markdown
          - usage_dict: dict décrivant l'utilisation des tokens (si disponible)
    """
    # Vérifier que la clé API est configurée
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise ValueError("OPENAI_API_KEY n'est pas configurée dans les settings")

    # Construire le message système
    system_message = (
        "Tu es un assistant expert en audit du secteur public. "
        "Tu es chargé de produire un Kit complet de préparation à l'audit, "
        "structuré et exploitable par un auditeur humain. "
        "Tu génères des documents professionnels en français, "
        "avec une structure claire et des recommandations pratiques."
    )

    # Construire le prompt utilisateur
    context_section = _build_context_section(inquiry)
    
    user_prompt = f"""{consignes_md}

## CONTEXTE DE LA DEMANDE

{context_section}

## DOCUMENTS FOURNIS

{documents_payload}

## INSTRUCTIONS

Génère un document Markdown structuré en français contenant :
1. Une introduction générale adaptée au contexte client
2. Des questionnaires de préparation adaptés aux documents fournis
3. Des tableaux d'irrégularités avec solutions pratiques
4. Une synthèse finale avec recommandations
5. Un plan d'action priorisé

Le document doit être professionnel, clair et directement utilisable pour préparer un audit.
Utilise des titres Markdown (##, ###) pour structurer le contenu.
"""

    # Configuration du client OpenAI
    client_kwargs = {"api_key": api_key}
    
    if hasattr(settings, "OPENAI_ORG") and settings.OPENAI_ORG:
        client_kwargs["organization"] = settings.OPENAI_ORG
    
    if hasattr(settings, "OPENAI_PROJECT") and settings.OPENAI_PROJECT:
        client_kwargs["project"] = settings.OPENAI_PROJECT
    
    if hasattr(settings, "OPENAI_BASE_URL") and settings.OPENAI_BASE_URL:
        client_kwargs["base_url"] = settings.OPENAI_BASE_URL

    client = OpenAI(**client_kwargs)

    # Déterminer le modèle à utiliser
    model = getattr(settings, "OPENAI_CHAT_MODEL", "gpt-4o-mini")
    fallbacks = getattr(
        settings,
        "OPENAI_CHAT_MODEL_FALLBACKS",
        ["gpt-4o", "gpt-4o-mini"]
    )
    models_to_try = [model] + [f for f in fallbacks if f != model]

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_prompt}
    ]

    # Appel API avec fallback
    response = None
    last_error = None
    used_model = None

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,  # Faible température pour plus de cohérence
                max_tokens=8000
            )
            used_model = model_name
            logger.info(f"Modèle OpenAI utilisé avec succès: {model_name}")
            break
        except OpenAIAPIError as e:
            # Extraire les informations d'erreur OpenAI
            error_code = getattr(e, "code", None)
            error_type = getattr(e, "type", None)
            error_message = str(e)
            
            # Construire un message d'erreur plus lisible
            if error_code == "insufficient_quota" or "429" in error_message or "quota" in error_message.lower():
                raise KitGenerationError(
                    "Quota OpenAI dépassé. Veuillez vérifier votre plan et vos informations de facturation.",
                    error_code="429",
                    error_details={"type": error_type, "message": error_message}
                )
            elif error_code == "invalid_api_key" or "401" in error_message or "authentication" in error_message.lower():
                raise KitGenerationError(
                    "Clé API OpenAI invalide ou manquante. Veuillez vérifier la configuration OPENAI_API_KEY.",
                    error_code="401",
                    error_details={"type": error_type, "message": error_message}
                )
            else:
                # Pour les autres erreurs OpenAI, propager avec un message plus clair
                last_error = KitGenerationError(
                    f"Erreur API OpenAI ({error_code or error_type}): {error_message}",
                    error_code=error_code,
                    error_details={"type": error_type, "message": error_message}
                )
                logger.warning(f"Erreur OpenAI avec le modèle {model_name}: {last_error}")
                if model_name == models_to_try[-1]:
                    raise last_error
        except Exception as e:
            last_error = e
            logger.warning(f"Erreur avec le modèle {model_name}: {e}")
            if model_name == models_to_try[-1]:
                raise

    if response is None:
        raise last_error or ValueError("Aucun modèle OpenAI n'a fonctionné")

    # Extraire le contenu généré
    markdown = response.choices[0].message.content

    # Construire le dict d'usage
    usage_dict = {
        "model": used_model,
        "total_tokens": None,
        "prompt_tokens": None,
        "completion_tokens": None,
    }

    if hasattr(response, "usage") and response.usage:
        usage = response.usage
        usage_dict["total_tokens"] = getattr(usage, "total_tokens", None)
        usage_dict["prompt_tokens"] = getattr(usage, "prompt_tokens", None)
        usage_dict["completion_tokens"] = getattr(usage, "completion_tokens", None)
        
        # Si c'est un objet Pydantic, essayer model_dump()
        if hasattr(usage, "model_dump"):
            usage_dict.update(usage.model_dump())

    return markdown, usage_dict


def _build_context_section(inquiry) -> str:
    """
    Construit la section de contexte à partir des champs de ClientInquiry.
    """
    lines = []
    
    if inquiry.organization_name:
        lines.append(f"- **Organisation** : {inquiry.organization_name}")
    
    if inquiry.statut_juridique:
        lines.append(f"- **Statut juridique** : {inquiry.statut_juridique}")
    
    if inquiry.location:
        lines.append(f"- **Localisation** : {inquiry.location}")
    
    if inquiry.sector:
        lines.append(f"- **Secteur** : {inquiry.sector}")
    
    if inquiry.audits_types:
        audits_str = ", ".join(inquiry.audits_types) if isinstance(inquiry.audits_types, list) else str(inquiry.audits_types)
        lines.append(f"- **Types d'audit** : {audits_str}")
    
    if inquiry.audits_frequency:
        lines.append(f"- **Fréquence des audits** : {inquiry.audits_frequency}")
    
    if inquiry.mission_text:
        lines.append(f"\n**Missions** :\n{inquiry.mission_text}")
    
    if inquiry.context_text:
        lines.append(f"\n**Contexte** :\n{inquiry.context_text}")
    
    if inquiry.notes_text:
        lines.append(f"\n**Notes** :\n{inquiry.notes_text}")
    
    return "\n".join(lines) if lines else "Aucune information contextuelle fournie."

