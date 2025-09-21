# backend/pages/admin.py
# Назначение: Управление статическими страницами в админке.

from django.contrib import admin
from .models import StaticPage


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}

