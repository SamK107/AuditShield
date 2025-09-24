# store/admin.py
from django.contrib import admin

from .models import (
    DownloadToken,
    ExampleSlide,
    IrregularityCategory,
    IrregularityRow,
    MediaAsset,
    OfferTier,
    Order,
    Product,
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


from .models import PreliminaryRow, PreliminaryTable


class PreliminaryRowInline(admin.TabularInline):
    model = PreliminaryRow
    extra = 1
    fields = ("order", "irregularity", "reference", "actors", "dispositions")
    show_change_link = True

@admin.register(PreliminaryTable)
class PreliminaryTableAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "group", "order")
    list_filter = ("product", "group")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PreliminaryRowInline]

@admin.register(ExampleSlide)
class ExampleSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "product", "order")
    list_filter = ("product",)
    search_fields = ("title", "irregularity", "legal_ref")
    list_editable = ("order",)
    ordering = ("product", "order", "id")

from .models import ClientInquiry, InquiryDocument


class InquiryDocumentInline(admin.TabularInline):
    model = InquiryDocument
    extra = 0
    readonly_fields = ("uploaded_at",)

@admin.register(ClientInquiry)
class ClientInquiryAdmin(admin.ModelAdmin):
    list_display = ("id","kind","organization_name","contact_name","email","created_at","status")
    list_filter = ("kind","status","statut_juridique","sector")
    search_fields = ("organization_name","contact_name","email","phone")
    inlines = [InquiryDocumentInline]

