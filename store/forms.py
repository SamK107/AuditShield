from django import forms
from .models import ClientInquiry

# Placeholders minimaux pour éviter ImportError dans store/views.py
# (À remplacer par les vraies implémentations si nécessaire)
class CheckoutForm(forms.Form):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    phone = forms.CharField(required=False)
    amount_fcfa = forms.IntegerField(required=False)


class PaymentForm(forms.Form):
    """
    Formulaire générique de paiement (pour CinetPay / Orange Money).
    Doit exposer first_name, last_name, email, phone, tier_id.
    """
    first_name = forms.CharField(required=True, max_length=120, label="Prénom")
    last_name = forms.CharField(required=True, max_length=120, label="Nom")
    email = forms.EmailField(required=True, label="Email")
    phone = forms.CharField(required=False, max_length=32, label="Téléphone")
    tier_id = forms.CharField(required=False, max_length=64)


FUNDING_CHOICES = [
    ("budget_etat", "Budget de l'État"),
    ("appuis_ptf", "Appuis/Projets (PTF, bailleurs)"),
    ("ressources_propres", "Ressources propres"),
    ("fonds_speciaux", "Fonds spéciaux / affectés"),
    ("dons_legs", "Dons & legs"),
    ("recettes_para", "Recettes parafiscales"),
]

AUDIT_TYPES_CHOICES = [
    ("interne_conformite", "Audit/Contrôle interne (conformité)"),
    ("interne_performance", "Audit interne (performance)"),
    ("externe_courdescomptes", "Contrôle externe (Cour des comptes/IGE)"),
    ("inspection_ministere", "Inspection ministérielle / contrôle hiérarchique"),
    ("financier", "Audit financier / certification"),
    ("passation_marches", "Contrôle marchés publics"),
    ("fraude_enquete", "Enquête / anti-fraude"),
]


class KitInquiryForm(forms.ModelForm):
    funding_sources = forms.MultipleChoiceField(
        required=False,
        choices=FUNDING_CHOICES,
        widget=forms.SelectMultiple(attrs={
            "size": 6,
            "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500"
        })
    )
    audits_types = forms.MultipleChoiceField(
        required=False,
        choices=AUDIT_TYPES_CHOICES,
        widget=forms.SelectMultiple(attrs={
            "size": 7,
            "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500"
        })
    )

    class Meta:
        model = ClientInquiry
        fields = [
            "contact_name", "email",
            "organization_name", "statut_juridique",
            "location", "sector", "budget_range",
            "mission_text",
            "context_text",
            "funding_sources", "audits_types", "audits_frequency",
            "staff_size", "org_chart_text", "notes_text",
        ]
        widgets = {
            "context_text": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Présentez le contexte : structure, service, missions, contraintes, objectifs...",
                "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialiser funding_sources et audits_types depuis le JSONField si instance existe
        if self.instance and self.instance.pk:
            self.fields["funding_sources"].initial = self.instance.funding_sources or []
            self.fields["audits_types"].initial = self.instance.audits_types or []

    def clean_funding_sources(self):
        return self.cleaned_data.get("funding_sources") or []

    def clean_audits_types(self):
        return self.cleaned_data.get("audits_types") or []

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.kind = ClientInquiry.KIND_KIT
        instance.funding_sources = self.cleaned_data.get("funding_sources", [])
        instance.audits_types = self.cleaned_data.get("audits_types", [])
        if commit:
            instance.save()
        return instance


class TrainingInquiryForm(forms.Form):
    contact_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False)
    topic = forms.CharField(required=False)
