from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.conf import settings
try:
    from PyPDF2 import PdfReader  # type: ignore
except Exception:
    PdfReader = None

class KitPreparationForm(forms.Form):
    order_ref = forms.CharField(label="Référence de commande (site)", max_length=128)
    email = forms.EmailField(label="Email d'achat")
    
    # Choix entre fichier PDF ou texte libre
    SUBMISSION_CHOICES = [
        ('file', 'Uploader un fichier PDF'),
        ('text', 'Coller le texte directement'),
    ]
    submission_type = forms.ChoiceField(
        choices=SUBMISSION_CHOICES,
        widget=forms.RadioSelect,
        initial='file',
        label="Comment souhaitez-vous soumettre votre texte ?"
    )
    
    file = forms.FileField(
        label="Votre fichier PDF",
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])],
        help_text="PDF uniquement, 4 pages max, 5 Mo max.",
        required=False
    )
    
    text_content = forms.CharField(
        label="Votre texte",
        widget=forms.Textarea(attrs={'rows': 15, 'placeholder': 'Collez votre texte ici...'}),
        help_text="Maximum 2500 mots.",
        required=False,
        max_length=20000  # Environ 2500 mots
    )
    
    accept_terms = forms.BooleanField(
        label="Je certifie avoir acheté l'ebook et que mon fichier respecte les conditions.",
        required=True
    )

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if not f:
            return f
            
        max_bytes = int(getattr(settings, "UPLOAD_MAX_BYTES", 5 * 1024 * 1024))
        if f.size > max_bytes:
            raise ValidationError("Fichier trop volumineux (max 5 Mo).")

        if PdfReader is not None:
            try:
                reader = PdfReader(f)
                pages = len(reader.pages)
            except Exception:
                raise ValidationError("PDF invalide ou non lisible.")
            finally:
                f.seek(0)
        else:
            pages = 1

        if pages > 4:
            raise ValidationError("Le PDF doit contenir au plus 4 pages.")
        return f

    def clean_text_content(self):
        text = self.cleaned_data.get("text_content", "")
        if not text:
            return text
            
        # Compter les mots (approximation simple)
        words = len(text.split())
        if words > 2500:
            raise ValidationError(f"Le texte contient {words} mots. Maximum autorisé : 2500 mots.")
        return text

    def clean(self):
        cleaned_data = super().clean()
        submission_type = cleaned_data.get("submission_type")
        file = cleaned_data.get("file")
        text_content = cleaned_data.get("text_content")

        if submission_type == "file" and not file:
            raise ValidationError("Veuillez sélectionner un fichier PDF.")
        
        if submission_type == "text" and not text_content:
            raise ValidationError("Veuillez saisir votre texte.")

        return cleaned_data
