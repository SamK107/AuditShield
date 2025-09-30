from django.contrib import admin

from .models import LegalDocument


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "doc_type", "slug", "status", "updated_at")
    list_filter = ("doc_type", "status", "updated_at")
    search_fields = ("title", "slug", "html_content")
    prepopulated_fields = {"slug": ("title",)}
