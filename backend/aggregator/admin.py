from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html

from .models import Source, Item
from .tasks import fetch_feed_for_source, fetch_all_feeds
from news.models import Category, News


class SourceAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "is_active", "created_at", "fetch_now_link")
    actions = ["fetch_selected_sources"]

    def fetch_now_link(self, obj):
        url = reverse("custom_admin:aggregator_source_fetch", args=[obj.pk])
        return format_html(f'<a class="button" href="{url}">Собрать</a>')
    fetch_now_link.short_description = "Действие"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:source_id>/fetch/",
                self.admin_site.admin_view(self.fetch_one),
                name="aggregator_source_fetch",
            ),
        ]
        return custom_urls + urls

    def fetch_one(self, request, source_id):
        source = Source.objects.get(pk=source_id)
        count = fetch_feed_for_source(source)
        self.message_user(
            request,
            f"Источник {source.title}: добавлено {count} новостей",
            level=messages.SUCCESS,
        )
        return redirect("..")

    def fetch_selected_sources(self, request, queryset):
        total_added = 0
        for source in queryset:
            count = fetch_feed_for_source(source)
            total_added += count
            self.message_user(
                request,
                f"Источник {source.title}: добавлено {count} новостей",
                level=messages.INFO,
            )
        self.message_user(
            request,
            f"Всего добавлено {total_added} новостей",
            level=messages.SUCCESS,
        )

    fetch_selected_sources.short_description = "Запустить парсинг для выбранных источников"


class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published_at", "created_at")
    search_fields = ("title", "summary")
    list_filter = ("source", "published_at")


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "created_at", "is_approved", "is_popular")
    list_filter = ("category", "is_approved", "is_popular", "is_moderated")
    search_fields = ("title", "content")
    date_hierarchy = "created_at"


class AggregatorAdminSite(admin.AdminSite):
    site_header = "IzotovLife Админка"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("fetch-feeds/", self.admin_view(self.fetch_feeds), name="fetch_feeds"),
        ]
        return custom_urls + urls

    def fetch_feeds(self, request):
        results = fetch_all_feeds()
        for src, res in results.items():
            self.message_user(request, f"{src}: {res}", messages.INFO)
        total = sum(v for v in results.values() if isinstance(v, int))
        self.message_user(request, f"Всего добавлено {total} новостей", messages.SUCCESS)
        return redirect("..")

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context["custom_buttons"] = [
            {"title": "Собрать все источники", "url": reverse("custom_admin:fetch_feeds")}
        ]
        return super().index(request, extra_context=extra_context)


# === Кастомный admin site и регистрация моделей ===
custom_admin_site = AggregatorAdminSite(name="custom_admin")

custom_admin_site.register(Source, SourceAdmin)
custom_admin_site.register(Item, ItemAdmin)
custom_admin_site.register(Category, CategoryAdmin)
custom_admin_site.register(News, NewsAdmin)
