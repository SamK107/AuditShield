from django.db import migrations


def seed_legal(apps, schema_editor):
    LegalDocument = apps.get_model("legal", "LegalDocument")
    defaults = [
        {
            "title": "Mentions légales",
            "slug": "mentions-legales",
            "doc_type": "mentions",
            "html_content": """
<h1 class="text-2xl font-bold mb-4">Mentions légales</h1>
<p><strong>Éditeur :</strong> Bloom Shield Gouvernance – auditsanspeur.com</p>
<p><strong>Responsable de la publication :</strong> Alex H.</p>
<p><strong>Siège :</strong> ACI 2000 Bamako-Mali</p>
<p><strong>Contact :</strong> <a class="underline" href="mailto:contact@auditsanspeur.com">contact@auditsanspeur.com</a></p>
<p><strong>Hébergeur :</strong> LWS</p>
<h2 class="text-xl font-semibold mt-6 mb-2">Propriété intellectuelle</h2>
<p>Textes, images, ebooks, modèles et éléments du site sont protégés par le droit d’auteur. Toute reproduction, représentation, adaptation, diffusion, traduction, exploitation, partielle ou totale, sans autorisation écrite préalable est interdite.</p>
<h2 class="text-xl font-semibold mt-6 mb-2">Données personnelles</h2>
<p>Les données collectées (commande, support) sont utilisées pour fournir les services. Vous disposez d’un droit d’accès, de rectification et de suppression via l’adresse de contact.</p>
<h2 class="text-xl font-semibold mt-6 mb-2">Cookies & mesure d’audience</h2>
<p>Nous utilisons uniquement des outils de mesure d’audience respectueux de la vie privée, sans cookies intrusifs ni suivi publicitaire. Voir la page “Cookies”.</p>
            """.strip(),
        },
        {
            "title": "Politique de confidentialité",
            "slug": "privacy",
            "doc_type": "privacy",
            "html_content": """
<h1 class="text-2xl font-bold mb-4">Politique de confidentialité</h1>
<p>Nous collectons uniquement les données nécessaires au traitement des commandes, au support client et à l’amélioration du service.</p>
<ul class="list-disc pl-6">
  <li><strong>Données traitées :</strong> identité, coordonnées, informations de commande/paiement (via prestataire), emails de support.</li>
  <li><strong>Base légale :</strong> exécution du contrat, intérêt légitime (amélioration), obligations légales.</li>
  <li><strong>Durées :</strong> limitées au nécessaire (conformité légale et fiscale).</li>
  <li><strong>Partage :</strong> prestataires techniques (hébergeur, paiement), dans la stricte mesure nécessaire.</li>
  <li><strong>Vos droits :</strong> accès, rectification, suppression. Contact : <a class="underline" href="mailto:contact@auditsanspeur.com">contact@auditsanspeur.com</a></li>
</ul>
<p>Nous n’effectuons pas de vente de données. Nous utilisons uniquement des outils de mesure d’audience respectueux de la vie privée, sans cookies intrusifs ni suivi publicitaire.</p>
            """.strip(),
        },
        {
            "title": "Politique Cookies",
            "slug": "cookies",
            "doc_type": "cookies",
            "html_content": """
<h1 class="text-2xl font-bold mb-4">Politique Cookies</h1>
<p>Ce site utilise des cookies strictement nécessaires (session, sécurité) et, le cas échéant, des cookies de mesure d’audience respectueux de la vie privée.</p>
<h2 class="text-xl font-semibold mt-6 mb-2">Types de cookies</h2>
<ul class="list-disc pl-6">
  <li><strong>Nécessaires :</strong> sécurité, session, panier.</li>
  <li><strong>Mesure d’audience :</strong> Nous utilisons uniquement des outils de mesure d’audience respectueux de la vie privée, sans cookies intrusifs ni suivi publicitaire.</li>
</ul>
<h2 class="text-xl font-semibold mt-6 mb-2">Gérer vos préférences</h2>
<p>Vous pouvez configurer votre navigateur pour refuser les cookies non essentiels. Si un bandeau de consentement est déployé, utilisez-le pour gérer vos choix.</p>
            """.strip(),
        },
    ]
    for d in defaults:
        LegalDocument.objects.get_or_create(slug=d["slug"], defaults=d)


def unseed(apps, schema_editor):
    LegalDocument = apps.get_model("legal", "LegalDocument")
    LegalDocument.objects.filter(slug__in=["mentions-legales", "privacy", "cookies"]).delete()


class Migration(migrations.Migration):
    dependencies = [("legal", "0001_initial")]
    operations = [migrations.RunPython(seed_legal, reverse_code=unseed)]
