from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from .models import LegalDocument

# Create your views here.


class LegalPageView(TemplateView):
    template_name = "legal/legal_page.html"
    slug = None  # set via as_view(slug="...")

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return view

    def dispatch(self, request, *args, **kwargs):
        self.slug = kwargs.get("slug") or self.slug
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        doc = get_object_or_404(LegalDocument, slug=self.slug, status="published")
        ctx["doc"] = doc
        return ctx


def mentions_modal(request):
    doc = get_object_or_404(LegalDocument, slug="mentions-legales", status="published")
    return render(request, "legal/_mentions_modal.html", {"doc": doc})
