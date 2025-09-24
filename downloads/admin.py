from django.contrib import admin
from django.apps import apps

from .models import DownloadableAsset, DownloadCategory, DownloadEntitlement, PurchaseClaim

DownloadCategory = apps.get_model('downloads', 'DownloadCategory')

@admin.register(DownloadCategory)
class DownloadCategoryAdmin(admin.ModelAdmin):
    list_display = ('slug', 'is_protected', 'required_sku')
    list_per_page = 50
    list_filter = ()  # can be extended later with a proper SimpleListFilter

    def is_protected(self, obj):
        val = getattr(obj, 'is_protected', None)
        if isinstance(val, bool):
            return val
        return bool(val)
    is_protected.boolean = True
    is_protected.short_description = "Protected?"

    def required_sku(self, obj):
        val = getattr(obj, 'required_sku', None)
        try:
            if hasattr(val, 'all'):
                return ", ".join(str(x) for x in val.all())
        except Exception:
            pass
        return "" if val is None else str(val)
    required_sku.short_description = "Required SKU(s)"


@admin.register(DownloadableAsset)
class DownloadableAssetAdmin(admin.ModelAdmin):
    list_display = (
        "title", "category", "get_ext", "is_published", "order", "updated_at"
    )
    exclude = ("order",)  # on ne demande pas 'order' dans le formulaire
    list_filter = ("category", "is_published")
    search_fields = ("title", "slug", "short_desc")
    ordering = ("category", "order", "-updated_at")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("updated_at", "created_at")

    

    def get_ext(self, obj):
        return obj.extension
    get_ext.short_description = "Ext."


@admin.register(DownloadEntitlement)
class DownloadEntitlementAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "category", "source", "created_at")
    list_filter = ("source", "category")
    search_fields = ("email", "user__username")


@admin.register(PurchaseClaim)
class PurchaseClaimAdmin(admin.ModelAdmin):
    list_display = ("email", "platform", "category", "status", "created_at")
    list_filter = ("platform", "status", "category")
    search_fields = ("email", "order_ref")
    actions = ["approve_claims", "reject_claims"]

    def approve_claims(self, request, queryset):
        from .models import DownloadEntitlement
        count = 0
        for c in queryset:
            if c.status != "APPROVED":
                DownloadEntitlement.objects.get_or_create(
                    email=c.email, category=c.category, defaults={"source": "EXT"}
                )
                c.status = "APPROVED"
                c.save()
                count += 1
        self.message_user(request, f"{count} demande(s) validée(s).")
    approve_claims.short_description = "Approuver et accorder l’accès"

    def reject_claims(self, request, queryset):
        updated = queryset.update(status="REJECTED")
        self.message_user(request, f"{updated} demande(s) rejetée(s).")
    reject_claims.short_description = "Rejeter"

