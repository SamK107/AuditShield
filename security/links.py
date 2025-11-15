from django.core.signing import TimestampSigner
from django.urls import reverse


def issue_bonus_start_link(*, order_ref: str, email: str, base_url: str, ttl_seconds: int = 60 * 60 * 24 * 7) -> str:
    """
    Génère un lien tokenisé pour /bonus/kit-preparation/start
    """
    signer = TimestampSigner(salt="bonus-kit-preparation")
    token = signer.sign(f"{order_ref}:{email}")
    # L'endpoint lit la TTL côté unsign (BONUS_TOKEN_AGE). Ici on fournit un token signé standard.
    path = reverse("store:bonus_submit")  # /bonus/kit-preparation/start
    return f"{base_url}{path}?product_slug=audit-sans-peur&token={token}"


