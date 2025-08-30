"""Admin registrations for aggregator models."""

from django.contrib import admin

from .models import Source, Item


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "url", "is_active", "format", "created_at")
    search_fields = ("title", "url")
    list_filter = ("is_active", "format")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source",
        "title",
        "link",
        "published_at",
        "created_at",
    )
    search_fields = ("title", "link", "guid")
    list_filter = ("source", "category")
    readonly_fields = ("content_hash",)

