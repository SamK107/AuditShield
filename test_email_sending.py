#!/usr/bin/env python
"""Script de test pour vérifier l'envoi d'emails"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.core.mail import EmailMessage
from django.conf import settings

# Test 1: Vérifier la configuration email
print("=== Configuration Email ===")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"CONTACT_INBOX_EMAIL: {getattr(settings, 'CONTACT_INBOX_EMAIL', 'NON DÉFINI')}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print()

# Test 2: Simuler l'envoi d'un email de test
print("=== Test d'envoi d'email ===")
to_email = getattr(settings, "CONTACT_INBOX_EMAIL", "contact@auditsanspeur.com")
subject = "[TEST] Bonus Kit Préparation - EXT-7777"
body = """Un client a soumis un texte pour le bonus Kit Préparation.

Référence: EXT-7777
Email: aloubs700@gmail.com

=== TEXTE SOUMIS ===
Ceci est un texte de test pour vérifier que l'email est bien envoyé.
"""

try:
    msg = EmailMessage(subject=subject, body=body, to=[to_email])
    msg.send(fail_silently=False)
    print(f"✅ Email test envoyé à {to_email}")
    print()
    print("NOTE: En mode développement (EMAIL_BACKEND=console),")
    print("      l'email sera affiché dans la console du serveur Django,")
    print("      pas envoyé réellement. C'est normal !")
except Exception as e:
    print(f"❌ Erreur: {e}")

