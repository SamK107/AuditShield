# core/views.py
from django.shortcuts import render
from store.models import ExampleSlide, OfferTier, Product
import re

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.utils.timezone import now

def home(request):
    product = Product.objects.filter(is_published=True).first()
    offers = OfferTier.objects.select_related("product").all()
    examples = ExampleSlide.objects.all()[:3]
    return render(
        request, "core/home.html", {"product": product, "offers": offers, "examples": examples}
    )


def about(request):
    return render(request, "core/about.html")


def policy(request):
    return render(request, "core/policy.html")


def cgv(request):
    return render(request, "core/cgv.html")


def contact(request):
    return render(request, "core/contact.html")
    

def coming_soon(request):
    return render(request, "core/landing_comingsoon.html", {
        "launch_window": "dans quelques jours",
        "coming_soon": True,              # <- active la logique de masquage dans base.html
    })

# --- Optionnel : capture d'email waitlist via HTMX ---
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def waitlist_signup(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Méthode non autorisée")

    email = (request.POST.get("email") or "").strip()
    name = (request.POST.get("name") or "").strip()

    if not email or not EMAIL_RE.match(email):
        msg = "❌ Merci d’indiquer un email valide."
        # HTMX => renvoyer du HTML lisible
        if request.headers.get("HX-Request") == "true":
            return HttpResponse(f'<span class="text-red-700">{msg}</span>', status=400)
        return HttpResponseBadRequest(msg)

    try:
        from .models import LaunchWaitlist
        LaunchWaitlist.objects.get_or_create(email=email, defaults={"name": name})
        msg = "✅ C’est noté ! Vous serez prévenu au lancement."
    except Exception:
        msg = "✅ Merci ! Nous vous informerons au lancement."

    # Si c'est une requête HTMX, renvoie un fragment HTML directement “swappable”
    if request.headers.get("HX-Request") == "true":
        return HttpResponse(f'<span class="text-green-700">{msg}</span>')

    # Sinon, garde l’API JSON (utile si appelée hors HTMX)
    return JsonResponse({"ok": True, "message": msg, "ts": now().isoformat()})
