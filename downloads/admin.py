from django.contrib import admin
from .models import DownloadableAsset, AssetCategory, Tag

@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = (
        "name", "slug"
    )  # <-- AJOUT OBLIGATOIRE pour autocomplete_fields


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(DownloadableAsset)
class DownloadableAssetAdmin(admin.ModelAdmin):
    list_display = (
        "title", "version", "visibility", "is_active", "ebook_code",
        "part_code", "chapter_code", "download_count", "updated_at"
    )
    list_filter = ("visibility", "is_active", "ebook_code", "category")
    search_fields = (
        "title", "description", "slug", "part_code", "chapter_code"
    )
    autocomplete_fields = ("category", "tags")
    readonly_fields = (
        "size_bytes", "sha256", "download_count", "last_download_at"
    )
    prepopulated_fields = {"slug": ("title",)}

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     # Exclure l'asset courant pour éviter qu'il ne se référence lui-même
    #     # (champ replaced_by supprimé)
    #     if request.resolver_match and request.resolver_match.kwargs.get("object_id"):
    #         current_id = request.resolver_match.kwargs["object_id"]
    #         kwargs["queryset"] = self.model.objects.exclude(pk=current_id)  # exclure l'asset courant
    #     else:
    #         kwargs["queryset"] = self.model.objects.all()
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

