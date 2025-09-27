# backend/news/admin.py
# Назначение: Админка для категорий, статей, импортированных новостей и источников.
# Обновлено:
#   - Используются source_fk и image.
#   - Превью логотипа источника и картинки новости.
#   - Фильтр по источнику с логотипами.
# Путь: backend/news/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count

from .models import Category, Article, ImportedNews, NewsSource


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "news_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(news_count_value=Count("importednews"))

    def news_count(self, obj):
        return obj.news_count_value
    news_count.short_description = "Кол-во новостей"


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "status", "created_at", "published_at")
    list_filter = ("status", "created_at", "published_at")
    search_fields = ("title", "content")
    date_hierarchy = "created_at"


@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "logo_preview")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 40px;"/>', obj.logo.url)
        return "—"
    logo_preview.short_description = "Логотип"


@admin.action(description="Отправить в архив")
def move_to_archive(modeladmin, request, queryset):
    queryset.update(archived_at=timezone.now())


@admin.action(description="Вернуть из архива")
def restore_from_archive(modeladmin, request, queryset):
    queryset.update(archived_at=None)


class SourceLogoFilter(admin.SimpleListFilter):
    title = "Источник (с логотипом)"
    parameter_name = "source_fk"

    def lookups(self, request, model_admin):
        sources = NewsSource.objects.all()
        lookups = []
        for src in sources:
            if src.logo:
                label = format_html('<img src="{}" style="height:20px; margin-right:5px;"/> {}',
                                    src.logo.url, src.name)
            else:
                label = src.name
            lookups.append((src.id, label))
        return lookups

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source_fk_id=self.value())
        return queryset


@admin.register(ImportedNews)
class ImportedNewsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source_fk",
        "category",
        "published_at",
        "created_at",
        "preview_image",
        "source_logo",
        "is_archived",
    )
    list_filter = (SourceLogoFilter, "category", "created_at", "archived_at")
    search_fields = ("title", "summary", "link")
    date_hierarchy = "published_at"
    readonly_fields = ("created_at",)
    actions = [move_to_archive, restore_from_archive]

    def is_archived(self, obj):
        return obj.archived_at is not None
    is_archived.boolean = True
    is_archived.short_description = "В архиве?"

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;"/>', obj.image)
        return "—"
    preview_image.short_description = "Картинка"

    def source_logo(self, obj):
        if obj.source_fk and obj.source_fk.logo:
            return format_html('<img src="{}" style="max-height: 30px;"/>', obj.source_fk.logo.url)
        return "—"
    source_logo.short_description = "Логотип источника"
