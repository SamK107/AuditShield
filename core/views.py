# core/views.py
import re

from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import render, redirect
from django.utils.timezone import now

from store.models import ExampleSlide, OfferTier, Product


def home(request):
    product = Product.objects.filter(is_published=True).first()
    offers = OfferTier.objects.select_related("product").all()
    examples = ExampleSlide.objects.all()[:3]

    

    return render(
        request,
        "core/home.html",
        {"product": product, "offers": offers, "examples": examples}
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
        "coming_soon": True,
    })


# --- Error handlers ---
def custom_404(request, exception, template_name="404.html"):
    """Custom 404 handler"""
    return render(request, template_name, status=404)


def custom_500(request, template_name="500.html"):
    """Custom 500 handler"""
    return render(request, template_name, status=500)


# --- TEMP: Test route for 500 error (remove in production) ---
def boom(request):
    """
    Temporary test view to trigger 500 error page.
    Visit /boom/ with DEBUG=False to see custom 500.html
    Remove this view and its URL after testing.
    """
    raise Exception("Intentional error for testing 500.html")


# --- Optionnel : capture d'email waitlist via HTMX ---
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def waitlist_signup(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Méthode non autorisée")

    email = (request.POST.get("email") or "").strip()
    name = (request.POST.get("name") or "").strip()

    if not email or not EMAIL_RE.match(email):
        msg = "❌ Merci d'indiquer un email valide."
        # HTMX => renvoyer du HTML lisible
        if request.headers.get("HX-Request") == "true":
            html = f'<span class="text-red-700">{msg}</span>'
            return HttpResponse(html, status=400)
        return HttpResponseBadRequest(msg)

    try:
        from .models import LaunchWaitlist
        LaunchWaitlist.objects.get_or_create(
            email=email, defaults={"name": name}
        )
        msg = "✅ C'est noté ! Vous serez prévenu au lancement."
    except Exception:
        msg = "✅ Merci ! Nous vous informerons au lancement."

    # Si c'est une requête HTMX, renvoie un fragment HTML
    if request.headers.get("HX-Request") == "true":
        html = f'<span class="text-green-700">{msg}</span>'
        return HttpResponse(html)

    # Sinon, redirige vers une page de confirmation dédiée
    return redirect("core:waitlist_success")


def waitlist_success(request):
    return render(request, "core/waitlist_success.html")
