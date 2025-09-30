from django import forms

from .models import ClientInquiry, Order

STATUTS = [
    ("Ministère", "Ministère"),
    ("Collectivité", "Collectivité"),
    ("ONG", "ONG"),
    ("Projet", "Projet"),
    ("EPIC", "EPIC"),
    ("EPA", "EPA"),
    ("Autre", "Autre"),
]
SECTEURS = [
    ("Santé", "Santé"),
    ("Éducation", "Éducation"),
    ("Développement rural", "Développement rural"),
    ("Infrastructures", "Infrastructures"),
    ("Multi-secteurs", "Multi-secteurs"),
    ("Autre", "Autre"),
]
BUDGETS = [("<500M", "< 500 M FCFA"), ("500M-5Md", "500 M – 5 Mds"), (">5Md", "> 5 Mds")]
FUNDING = [
    ("Budget État", "Budget État"),
    ("Bailleurs", "Bailleurs"),
    ("Recettes propres", "Recettes propres"),
    ("Cotisations/Dons", "Cotisations / Dons"),
    ("Autre", "Autre"),
]
AUDITS = [
    ("Cour des comptes", "Cour des comptes"),
    ("IGF/Inspection", "Inspection des finances / Contrôle"),
    ("Audit interne", "Audit interne"),
    ("Bailleur", "Bailleur"),
    ("Autre", "Autre"),
]
FREQ = [("récemment", "Récemment"), ("régulièrement", "Régulièrement"), ("rarement", "Rarement")]
STAFF = [("petite", "Petite"), ("moyenne", "Moyenne"), ("grande", "Grande")]


class BaseInquiryForm(forms.ModelForm):
    funding_sources = forms.MultipleChoiceField(
        required=False,
        choices=FUNDING,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "accent-emerald-600 focus:ring-2 focus:ring-emerald-400"}
        ),
    )
    audits_types = forms.MultipleChoiceField(
        required=False,
        choices=AUDITS,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "accent-blue-600 focus:ring-2 focus:ring-blue-400"}
        ),
    )

    class Meta:
        model = ClientInquiry
        fields = [
            "organization_name",
            "statut_juridique",
            "mission_text",
            "location",
            "sector",
            "budget_range",
            "funding_sources",
            "audits_types",
            "audits_frequency",
            "staff_size",
            "org_chart_text",
            "contact_name",
            "email",
            "phone",
            "notes_text",
        ]
        widgets = {
            "organization_name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500"
                }
            ),
            "statut_juridique": forms.Select(
                choices=STATUTS,
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500 bg-white"
                },
            ),
            "mission_text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500"
                }
            ),
            "sector": forms.Select(
                choices=SECTEURS,
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500 bg-white"
                },
            ),
            "budget_range": forms.Select(
                choices=BUDGETS,
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500 bg-white"
                },
            ),
            "audits_frequency": forms.Select(
                choices=FREQ,
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500 bg-white"
                },
            ),
            "staff_size": forms.Select(
                choices=STAFF,
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500 bg-white"
                },
            ),
            "org_chart_text": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500",
                }
            ),
            "contact_name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500"
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500"
                }
            ),
            "notes_text": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full px-3 py-2 rounded-xl border border-slate-300 focus:border-blue-500",
                }
            ),
        }


class KitInquiryForm(BaseInquiryForm):
    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.kind = ClientInquiry.KIND_KIT
        obj.payload = self.cleaned_data
        if commit:
            obj.save()
        return obj


DELIVERY_CHOICES = [
    ("presentiel", "Présentiel"),
    ("distanciel", "Distanciel"),
    ("hybride", "Hybride"),
]

PROGRAM_TITLE = (
    "Comprendre l’audit, se préparer à recevoir les missions d’audit, "
    "et transformer l’audit en opportunité de progrès — méthodes & outils pratiques"
)

ALLOWED_EXTS = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}
MAX_FILES = 5
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo


class TrainingInquiryForm(forms.Form):
    # Programme figé (non modifiable par l'utilisateur)
    program_title = forms.CharField(initial=PROGRAM_TITLE, required=False, widget=forms.HiddenInput)

    # Étape 1 — Essentiel (obligatoires)
    contact_name = forms.CharField(label="Nom et prénom", max_length=120, required=True)
    email = forms.EmailField(label="Email professionnel", required=True)
    organization_name = forms.CharField(
        label="Organisation / Structure", max_length=160, required=True
    )

    # Remplace l’ancien “topic” par un message de contexte clair
    message = forms.CharField(
        label="Votre contexte & objectifs (en quelques phrases)",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": (
                    "Ex. Entité publique (DG Budget) — mission IGF prévue en novembre ; "
                    "priorités : préparation des pièces justificatives, registre des risques, "
                    "revue des procédures & modèles adaptés."
                ),
            }
        ),
        required=True,
    )

    # Étape 2 — Détails (facultatifs)
    phone = forms.CharField(label="Téléphone", max_length=40, required=False)
    participants_count = forms.IntegerField(
        label="Nombre de participants (estimé)", min_value=1, required=False
    )
    delivery_mode = forms.ChoiceField(
        label="Format souhaité", choices=DELIVERY_CHOICES, required=False
    )
    preferred_dates = forms.CharField(
        label="Période cible (mois/dates approximatives)", max_length=120, required=False
    )
    # documents supprimé : géré côté vue/template
    website = forms.CharField(label="Site web (ne pas remplir)", required=False)

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam détecté.")
        return ""

    def clean(self):
        cleaned = super().clean()
        return cleaned


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["email", "first_name", "last_name", "phone"]
        widgets = {
            "email": forms.EmailInput(
                attrs={"class": "w-full px-3 py-2 rounded-xl border", "placeholder": "Votre email"}
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border",
                    "placeholder": "Prénom (optionnel)",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border",
                    "placeholder": "Nom (optionnel)",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 rounded-xl border",
                    "placeholder": "Téléphone (optionnel)",
                }
            ),
        }
