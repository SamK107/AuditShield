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
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "email", "amount_fcfa", "currency", "status", "provider_ref", "cinetpay_payment_id", "created_at", "paid_at")
    list_filter = ("status", "currency", "created_at", "paid_at")
    search_fields = ("id", "provider_ref", "cinetpay_payment_id", "email", "product__title")
    readonly_fields = ("created_at", "paid_at")
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


from .models import ClientInquiry, InquiryDocument, KitProcessingTask


class InquiryDocumentInline(admin.TabularInline):
    model = InquiryDocument
    extra = 0
    readonly_fields = ("uploaded_at",)


@admin.register(ClientInquiry)
class ClientInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "kind",
        "organization_name",
        "contact_name",
        "email",
        "created_at",
        "status",
    )
    list_filter = ("kind", "status", "statut_juridique", "sector")
    search_fields = ("organization_name", "contact_name", "email", "phone")
    inlines = [InquiryDocumentInline]


@admin.register(KitProcessingTask)
class KitProcessingTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "inquiry",
        "status",
        "created_at",
        "finished_at",
        "published_at",
        "published_by",
    )
    list_filter = ("status",)
    search_fields = ("inquiry__email", "inquiry__contact_name", "inquiry__organization_name")
    readonly_fields = ("id", "created_at", "started_at", "finished_at", "published_at")
    
    fieldsets = (
        ("Informations générales", {
            "fields": ("id", "inquiry", "status")
        }),
        ("Fichiers", {
            "fields": ("word_file", "pdf_file")
        }),
        ("Traitement", {
            "fields": ("prompt_md", "error", "created_at", "started_at", "finished_at")
        }),
        ("Publication", {
            "fields": ("published_at", "published_by")
        }),
    )
