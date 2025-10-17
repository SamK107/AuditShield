from django import forms
from django.core.exceptions import ValidationError
from .models import BonusRequest

class BonusRequestForm(forms.ModelForm):
    """
    Formulaires BonusRequest :
    - Règle: fournir order_ref OU proof_file (au moins un)
    - uploaded_text est requis
    - product_slug peut être prérempli par la vue
    """
    class Meta:
        model = BonusRequest
        fields = [
            "product_slug",
            "order_ref",
            "purchaser_email",
            "purchaser_name",
            "delivery_email",
            "service_role",
            "service_mission",
            "uploaded_text",
            "proof_file",
        ]

    def clean(self):
        cleaned = super().clean()
        order_ref = cleaned.get("order_ref")
        proof_file = cleaned.get("proof_file")
        uploaded_text = cleaned.get("uploaded_text")

        if not uploaded_text:
            raise ValidationError("Veuillez joindre votre texte (≤ 3 pages).")

        if not order_ref and not proof_file:
            raise ValidationError(
                "Fournissez l’ID/la référence de commande OU une preuve d’achat (PDF/PNG/JPG)."
            )
        return cleaned
