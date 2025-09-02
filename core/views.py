# core/views.py
from django.shortcuts import render
from store.models import Product, OfferTier, ExampleSlide

def home(request):
    product = Product.objects.filter(is_published=True).first()
    offers = OfferTier.objects.select_related("product").all()
    examples = ExampleSlide.objects.all()[:3]
    return render(request, "core/home.html", {"product": product, "offers": offers, "examples": examples})

def about(request):
    return render(request, "core/about.html")

def policy(request):
    return render(request, "core/policy.html")

def cgv(request):
    return render(request, "core/cgv.html")

def contact(request):
    return render(request, "core/contact.html")
