# store/admin.py
from django.contrib import admin
from .models import Product, OfferTier, ExampleSlide, MediaAsset, Order, DownloadToken

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "price_fcfa", "is_published")
    prepopulated_fields = {"slug": ("title",)}

admin.site.register(OfferTier)
admin.site.register(ExampleSlide)
admin.site.register(MediaAsset)
admin.site.register(Order)
admin.site.register(DownloadToken)
