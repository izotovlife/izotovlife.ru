# Путь: backend/news/apps.py
# Назначение: Конфигурация приложения news + подключение сигналов при старте Django.
# ВАЖНО: в settings.py укажите 'news.apps.NewsConfig' в INSTALLED_APPS.
# ИЗМЕНЕНИЯ: удалена дублирующая декларация класса NewsConfig (это необходимо для корректной работы).

from django.apps import AppConfig

class NewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "news"
    verbose_name = "Новости"

    def ready(self):
        # Подключаем пакет сигналов. Сам пакет импортирует все ресиверы внутри.
        from . import signals  # noqa: F401
