from django import forms

# Placeholders minimaux pour éviter ImportError dans store/views.py
# (À remplacer par les vraies implémentations si nécessaire)
class CheckoutForm(forms.Form):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    phone = forms.CharField(required=False)
    amount_fcfa = forms.IntegerField(required=False)

class KitInquiryForm(forms.Form):
    contact_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False)
    organization_name = forms.CharField(required=False)

class TrainingInquiryForm(forms.Form):
    contact_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)
    phone = forms.CharField(required=False)
    topic = forms.CharField(required=False)
