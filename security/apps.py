# Путь: backend/security/apps.py
# Назначение: Конфиг приложения security + безопасное подключение сигналов (logout очищает флаг админ-сессии).
# Примечание: используем importlib.import_module, чтобы не падать, если файла signals.py временно нет.

from django.apps import AppConfig
from importlib import import_module

class SecurityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "security"
    verbose_name = "Безопасность"

    def ready(self):
        # Безопасный импорт: если файла нет — просто не подключаем (не ломаем запуск)
        try:
            import_module("security.signals")
        except ModuleNotFoundError:
            # Можно логировать, но не критично:
            # print("security.signals not found — skip")
            pass




