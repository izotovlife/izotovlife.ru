# backend/news/admin.py
# Назначение: Админка для категорий, авторских статей и импортированных новостей.
# Путь: backend/news/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count

from .models import Category, Article, ImportedNews


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "news_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # аннотируем количество новостей (ImportedNews) в каждой категории
        return qs.annotate(news_count_value=Count("importednews"))

    def news_count(self, obj):
        return obj.news_count_value
    news_count.short_description = "Кол-во новостей"


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "created_at", "published_at")
    list_filter = ("status", "created_at", "published_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"


# ==== Actions для ImportedNews ====
@admin.action(description="Отправить в архив")
def move_to_archive(modeladmin, request, queryset):
    queryset.update(archived_at=timezone.now())


@admin.action(description="Вернуть из архива")
def restore_from_archive(modeladmin, request, queryset):
    queryset.update(archived_at=None)


@admin.register(ImportedNews)
class ImportedNewsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source",
        "category",
        "published_at",
        "created_at",
        "preview_image",
        "is_archived",
    )
    list_filter = ("source", "category", "created_at", "archived_at")
    search_fields = ("title", "summary", "source")
    date_hierarchy = "published_at"
    readonly_fields = ("created_at",)
    actions = [move_to_archive, restore_from_archive]

    def is_archived(self, obj):
        return obj.archived_at is not None
    is_archived.boolean = True
    is_archived.short_description = "В архиве?"

    def preview_image(self, obj):
        """Мини-превью картинки в админке."""
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.image)
        return "—"
    preview_image.short_description = "Картинка"
