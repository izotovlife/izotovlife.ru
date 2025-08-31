# backend/news/admin.py

from django.contrib import admin
from .models import Category, News


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")   # исправлено: было "title"
    prepopulated_fields = {"slug": ("name",)}  # исправлено: было "title"


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "created_at", "is_approved", "is_popular")
    list_filter = ("category", "is_approved", "is_popular", "is_moderated")
    search_fields = ("title", "content")
    date_hierarchy = "created_at"
