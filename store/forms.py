from django import forms


class CheckoutForm(forms.Form):
    email = forms.EmailField(label="Email")
    first_name = forms.CharField(label="Prénom", max_length=120)
    last_name = forms.CharField(label="Nom", max_length=120)
    phone = forms.CharField(label="Téléphone", max_length=32, required=False)
    tier_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
