from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import OfferTier, Product


class Command(BaseCommand):
    help = "Ajuste les 3 offres: titres marketing, features, popularité (Standard uniquement)."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        product = Product.objects.filter(is_published=True).first()
        if not product:
            self.stdout.write(self.style.WARNING("Aucun product publié."))
            return
        tiers = list(OfferTier.objects.filter(product=product))
        if not tiers:
            self.stdout.write(self.style.WARNING("Aucun OfferTier."))
            return
        standard = kit = formation = None
        for t in tiers:
            label = (getattr(t, "get_kind_display", lambda: "")() or t.title or "").lower()
            combo = " ".join([getattr(t,"slug","") or "", t.title or "", label])
            if "ebook" in combo or "standard" in combo: standard = t
            elif "personnalis" in combo or "kit" in combo or "adapt" in combo: kit = t
            elif "formation" in combo or "assistance" in combo: formation = t
        changed = 0
        if standard:
            standard.title = "Ebook Audit Sans Peur"
            if hasattr(standard,"price_fcfa") and not standard.price_fcfa: standard.price_fcfa = 15000
            standard.is_popular = True
            if hasattr(standard,"features_json"):
                standard.features_json = [
                    "Guide des réponses audit (bonus)",
                    "Kit préparation audit — bonus (texte client ≤ 3 pages)",
                    "Garantie 7 jours",
                    "Accès immédiat",
                    "Support email",
                ]
            standard.save(); changed += 1
        if kit:
            kit.title = "Kit complet de préparation à l’audit"
            kit.is_popular = False
            if hasattr(kit,"features_json"):
                kit.features_json = [
                    "Dossier irrégularités adapté",
                    "Disponible sous 72 heures",
                    "Garantie 7 jours",
                    "Support email",
                ]
            kit.save(); changed += 1
        if formation:
            formation.title = "Bouclier contre irrégularité et fautes de gestion"
            formation.is_popular = False
            if hasattr(formation,"features_json"):
                formation.features_json = [
                    "Ateliers sur cas réels",
                    "Simulations Q/R avec auditeurs",
                    "Assistance post-formation",
                    "Support email",
                ]
            formation.save(); changed += 1
        self.stdout.write(self.style.SUCCESS(f"Offres ajustées: {changed}"))
