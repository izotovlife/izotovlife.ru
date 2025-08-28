# ===== ФАЙЛ: backend/news/admin.py =====
# ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\backend\\news\\admin.py
# НАЗНАЧЕНИЕ: Настройки Django admin для моделей News и Category.
# ОПИСАНИЕ: Добавляет кнопку запуска RSS-парсера в список новостей.

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.core.management import call_command

from .models import News, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "is_moderated")
    list_filter = ("is_moderated", "category")
    search_fields = ("title",)
    change_list_template = "admin/news_change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "fetch-rss/",
                self.admin_site.admin_view(self.fetch_rss),
                name="news-fetch-rss",
            )
        ]
        return custom + urls

    def fetch_rss(self, request):
        call_command("fetch_rss")
        self.message_user(request, "RSS загрузка завершена", messages.SUCCESS)
        return redirect("..")
