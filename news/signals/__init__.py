# Путь: backend/news/signals/__init__.py
# Назначение: Инициализация пакета сигналов приложения news.
# При импорте пакета (см. apps.py → ready()) автоматически подключаются все ресиверы.

from . import strip_read_more  # noqa: F401
