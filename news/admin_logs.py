# Путь: backend/news/admin_logs.py
# Назначение: Админка для логов (NewsResolverLog и RSSImportLog).
# Фишки:
#   ✅ Цветные бейджи уровней (INFO, WARNING, ERROR).
#   ✅ Поиск, фильтры, сортировка.
#   ✅ Действие: "Очистить старые логи (30 дней)".
#   ✅ Кнопка "🗑 Удалить все логи" прямо в админке.
#   ✅ Совместимо с Django 5+.

from datetime import timedelta
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect

from .models_logs import NewsResolverLog, RSSImportLog


# ==========================
# ОБЩАЯ ФУНКЦИЯ ОЧИСТКИ СТАРЫХ ЛОГОВ
# ==========================
def clear_old_logs(modeladmin, request, queryset):
    """Удаляет логи старше 30 дней."""
    days = 30
    threshold = timezone.now() - timedelta(days=days)
    model = modeladmin.model
    old_logs = model.objects.filter(created_at__lt=threshold)
    count = old_logs.count()
    old_logs.delete()
    modeladmin.message_user(
        request,
        f"Удалено {count} записей из {model.__name__} (старше {days} дней).",
    )


clear_old_logs.short_description = "🧹 Очистить логи старше 30 дней"


# ==========================
# RSS IMPORT LOG ADMIN
# ==========================
@admin.register(RSSImportLog)
class RSSImportLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "colored_level", "source_name", "short_message")
    list_filter = ("level", "source_name")
    search_fields = ("message", "source_name")
    readonly_fields = ("created_at", "source_name", "message", "level")
    actions = [clear_old_logs]

    def colored_level(self, obj):
        colors = {"INFO": "green", "WARNING": "orange", "ERROR": "red"}
        color = colors.get(obj.level, "gray")
        return format_html(f'<b style="color:{color}">{obj.level}</b>')
    colored_level.short_description = "Уровень"

    def short_message(self, obj):
        return (obj.message[:100] + "…") if len(obj.message) > 100 else obj.message
    short_message.short_description = "Сообщение"

    # ===== Кнопка “Удалить все логи” =====
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "clear-all/",
                self.admin_site.admin_view(self.clear_all_logs),
                name="rssimportlog_clear_all",
            ),
        ]
        return custom_urls + urls

    def clear_all_logs(self, request):
        count, _ = RSSImportLog.objects.all().delete()
        messages.success(request, f"Удалено {count} логов из RSSImportLog.")
        return redirect("..")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["custom_button_label"] = "🗑 Удалить все логи"
        extra_context["custom_button_url"] = "clear-all/"
        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        js = ["admin/custom_admin_button.js"]


# ==========================
# NEWS RESOLVER LOG ADMIN
# ==========================
@admin.register(NewsResolverLog)
class NewsResolverLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "colored_level", "slug", "short_message")
    list_filter = ("level", "created_at")
    search_fields = ("slug", "message")
    ordering = ("-created_at",)
    actions = [clear_old_logs]
    readonly_fields = ("created_at", "slug", "level", "message")

    def colored_level(self, obj):
        colors = {"INFO": "green", "WARNING": "orange", "ERROR": "red"}
        color = colors.get(obj.level, "gray")
        return format_html(f'<b style="color:{color}">{obj.level}</b>')
    colored_level.short_description = "Уровень"

    def short_message(self, obj):
        return (obj.message[:80] + "…") if len(obj.message) > 80 else obj.message
    short_message.short_description = "Сообщение"

    # ===== Кнопка “Удалить все логи” =====
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "clear-all/",
                self.admin_site.admin_view(self.clear_all_logs),
                name="newsresolverlog_clear_all",
            ),
        ]
        return custom_urls + urls

    def clear_all_logs(self, request):
        count, _ = NewsResolverLog.objects.all().delete()
        messages.success(request, f"Удалено {count} логов из NewsResolverLog.")
        return redirect("..")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["custom_button_label"] = "🗑 Удалить все логи"
        extra_context["custom_button_url"] = "clear-all/"
        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        js = ["admin/custom_admin_button.js"]
