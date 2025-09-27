# backend/news/apps.py
# Назначение: AppConfig, чтобы подцепить signals при старте Django.
# ВАЖНО: в settings.py замените 'news' на 'news.apps.NewsConfig'
# Путь: backend/news/apps.py

from django.apps import AppConfig

class NewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "news"
    verbose_name = "Новости"

    def ready(self):
        # подключаем сигналы
        from . import signals  # noqa: F401
