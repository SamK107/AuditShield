# store/admin.py
from django.contrib import admin
from .models import (
    Product, OfferTier, ExampleSlide, MediaAsset,
    Order, DownloadToken, IrregularityCategory, IrregularityRow
)

class ExampleSlideInline(admin.StackedInline):
    model = ExampleSlide
    extra = 0

class IrregularityCategoryInline(admin.TabularInline):
    model = IrregularityCategory
    extra = 0
    fields = ("title", "slug", "group", "order")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "price_fcfa", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ExampleSlideInline, IrregularityCategoryInline]

class IrregularityRowInline(admin.TabularInline):
    model = IrregularityRow
    extra = 0
    fields = ("order", "version", "irregularity", "reference", "actors", "dispositions")

@admin.register(IrregularityCategory)
class IrregularityCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "group", "order")
    list_filter = ("group", "product")
    search_fields = ("title", "product__title")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [IrregularityRowInline]

admin.site.register(OfferTier)
admin.site.register(MediaAsset)
admin.site.register(Order)
admin.site.register(DownloadToken)
