from django.contrib import admin
from .models import DownloadableAsset, AssetCategory, Tag

@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")  # <-- AJOUT OBLIGATOIRE pour autocomplete_fields

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(DownloadableAsset)
class DownloadableAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "version", "visibility", "is_active", "ebook_code", "part_code", "chapter_code", "download_count", "updated_at")
    list_filter = ("visibility", "is_active", "ebook_code", "category")
    search_fields = ("title", "description", "slug", "part_code", "chapter_code")
    autocomplete_fields = ("category", "tags", "replaced_by")
    readonly_fields = ("size_bytes", "sha256", "download_count", "last_download_at")

