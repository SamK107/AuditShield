# store/utils/tokens.py
"""
Utilitaires pour la gestion des tokens de téléchargement signés.
"""
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.utils import timezone
from datetime import timedelta

from store.models import DownloadToken, ClientInquiry


def issue_download_token(inquiry: ClientInquiry, ttl_minutes: int = 45) -> DownloadToken:
    """
    Génère un token de téléchargement signé pour une inquiry.
    
    Args:
        inquiry: Instance ClientInquiry
        ttl_minutes: Durée de vie du token en minutes (défaut: 45)
    
    Returns:
        DownloadToken créé
    """
    signer = TimestampSigner()
    token = signer.sign(str(inquiry.id))
    expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
    
    dt = DownloadToken.objects.create(
        inquiry=inquiry,
        token=token,
        expires_at=expires_at,
        max_uses=1,
        used_count=0,
    )
    
    return dt


def validate_download_token(token: str) -> int | None:
    """
    Valide un token de téléchargement et retourne l'ID de l'inquiry.
    
    Args:
        token: Token signé
    
    Returns:
        ID de l'inquiry si valide, None sinon
    """
    signer = TimestampSigner()
    try:
        val = signer.unsign(token, max_age=3600)  # 60 min max
        return int(val)
    except (BadSignature, SignatureExpired, ValueError):
        return None


def consume_token(token_str: str) -> DownloadToken | None:
    """
    Consomme un token (incrémente used_count) si valide et non expiré.
    
    Args:
        token_str: Token à consommer
    
    Returns:
        DownloadToken si valide et consommable, None sinon
    """
    inquiry_id = validate_download_token(token_str)
    if not inquiry_id:
        return None
    
    try:
        dt = DownloadToken.objects.select_for_update().get(
            token=token_str,
            inquiry_id=inquiry_id,
        )
        
        # Vérifier expiration et limite d'utilisation
        if not dt.is_valid():
            return None
        
        # Incrémenter le compteur
        dt.used_count += 1
        dt.save(update_fields=["used_count"])
        
        return dt
        
    except DownloadToken.DoesNotExist:
        return None

