# Путь: backend/image_guard/apps.py
# Назначение: Конфиг приложения. При старте Django подключает сигналы image_guard.

from django.apps import AppConfig


class ImageGuardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "image_guard"
    verbose_name = "Image Guard (проверка картинок)"

    def ready(self):
        # Важно: подключаем обработчики сигналов при старте приложения
        from . import signals  # noqa: F401

