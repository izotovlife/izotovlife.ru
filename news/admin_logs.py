# backend/news/admin_logs.py
# Назначение: Админка для модели NewsResolverLog (логи резолвера slug).
# Фишки:
#   - Цветные бейджи уровней (INFO, WARNING, ERROR).
#   - Поиск по slug и тексту сообщения.
#   - Фильтр по уровню и дате.
#   - Укороченное сообщение в списке.
#   - Сортировка: новые записи сверху.

from django.contrib import admin
from django.utils.html import format_html
from .models_logs import NewsResolverLog


@admin.register(NewsResolverLog)
class NewsResolverLogAdmin(admin.ModelAdmin):
    # какие колонки показываем в списке
    list_display = ("created_at", "level_colored", "slug", "short_message")
    # фильтры справа
    list_filter = ("level", "created_at")
    # строка поиска сверху
    search_fields = ("slug", "message")
    # сортировка по умолчанию: новые сверху
    ordering = ("-created_at",)

    def level_colored(self, obj):
        """Показать уровень с цветом"""
        colors = {
            "INFO": "green",
            "WARNING": "orange",
            "ERROR": "red",
        }
        color = colors.get(obj.level, "gray")
        return format_html(f'<b><span style="color:{color}">{obj.level}</span></b>')
    level_colored.short_description = "Уровень"

    def short_message(self, obj):
        """Обрезать длинное сообщение"""
        return (obj.message[:80] + "...") if len(obj.message) > 80 else obj.message
    short_message.short_description = "Сообщение"
