# Путь: backend/news/models_logs.py
# Назначение: модели для хранения логов резолвера slug и логов операций (RSS/команды).
# ✅ Исправлено: нет самоуказующего импорта; только объявления моделей.
# ✅ Порядок: сначала NewsResolverLog, затем RSSImportLog (c timezone).

from django.db import models
from django.utils import timezone


class NewsResolverLog(models.Model):
    """Логи резолвера slug (для отладки маршрутизации/поиска страниц/новостей)."""
    created_at = models.DateTimeField("Создано", auto_now_add=True, db_index=True)
    level = models.CharField("Уровень", max_length=20, db_index=True)
    slug = models.CharField("Слаг", max_length=255, db_index=True)
    message = models.TextField("Сообщение")

    class Meta:
        verbose_name = "Лог резолвера"
        verbose_name_plural = "Логи резолвера"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.level}] {self.slug} @ {self.created_at:%Y-%m-%d %H:%M}"


class RSSImportLog(models.Model):
    """Логи импорта RSS-источников и фоновых management-команд."""
    created_at = models.DateTimeField("Время", default=timezone.now, db_index=True)
    source_name = models.CharField("Источник", max_length=255, db_index=True)
    message = models.TextField("Сообщение")
    level = models.CharField(
        "Уровень",
        max_length=20,
        choices=[("INFO", "Инфо"), ("WARNING", "Предупреждение"), ("ERROR", "Ошибка")],
        default="INFO",
        db_index=True,
    )

    class Meta:
        verbose_name = "Лог импорта RSS"
        verbose_name_plural = "Логи импорта RSS"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source_name", "-created_at"], name="rsslog_src_time_idx"),
        ]

    def __str__(self):
        # короткий префикс, чтобы список читался
        return f"[{self.level}] {self.source_name}: {self.message[:80]}"
