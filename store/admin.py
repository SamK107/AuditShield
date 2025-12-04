# store/admin.py
from django.contrib import admin

from .models import (
    ClientInquiry,
    DownloadToken,
    ExampleSlide,
    GeneratedDraft,
    IrregularityCategory,
    IrregularityRow,
    KitOrder,
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
        "processing_state",
        "payment_status",
        "created_at",
        "status",
    )
    list_filter = ("kind", "status", "processing_state", "payment_status", "statut_juridique", "sector", "created_at")
    search_fields = ("organization_name", "contact_name", "email", "phone")
    readonly_fields = ("created_at",)
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


@admin.register(KitOrder)
class KitOrderAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_id",
        "full_name",
        "email",
        "offer",
        "status",
        "amount",
        "created_at",
        "delivery_date",
    )
    list_filter = ("status", "offer", "created_at", "delivery_date")
    search_fields = ("tracking_id", "email", "full_name")
    readonly_fields = ("tracking_id", "created_at", "updated_at")
    
    fieldsets = (
        ("Informations générales", {
            "fields": (
                "tracking_id",
                "full_name",
                "email",
                "offer",
                "amount",
            )
        }),
        ("Suivi", {
            "fields": (
                "status",
                "estimated_delay_hours",
                "delivery_date",
                "starter_pack_delivered",
            )
        }),
        ("Relations", {
            "fields": ("inquiry", "order"),
            "classes": ("collapse",),
        }),
        ("Dates", {
            "fields": ("created_at", "updated_at"),
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Rendre tracking_id readonly uniquement si l'objet existe."""
        readonly = list(self.readonly_fields)
        if obj:  # Si l'objet existe déjà
            readonly.append("tracking_id")
        return readonly


@admin.register(GeneratedDraft)
class GeneratedDraftAdmin(admin.ModelAdmin):
    list_display = ("id", "inquiry", "model_name", "token_usage", "created_at")
    list_filter = ("created_at", "model_name")
    search_fields = ("inquiry__contact_name", "inquiry__email", "inquiry__organization_name")
    readonly_fields = ("created_at", "built_at")
    
    fieldsets = (
        ("Informations générales", {
            "fields": ("inquiry", "created_at", "built_at")
        }),
        ("Génération IA", {
            "fields": ("model_name", "token_usage", "log")
        }),
        ("Fichier", {
            "fields": ("docx",)
        }),
    )
