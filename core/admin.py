# core/admin.py
from django.contrib import admin
from .models import LaunchWaitlist

@admin.register(LaunchWaitlist)
class LaunchWaitlistAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "created_at", "source")
    search_fields = ("email", "name")
    list_filter = ("created_at",)
# Register your models here.
