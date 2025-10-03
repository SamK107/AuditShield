from django.shortcuts import render
from django.http import HttpRequest

def manual_claim(request: HttpRequest):
    slug = request.GET.get("slug", "")
    email = request.GET.get("email", "")
    return render(request, "downloads/manual_claim.html", {"slug": slug, "email": email})
