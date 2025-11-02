# Путь: backend/rssfeed/__init__.py
# Назначение: Инициализация пакета rssfeed. Тихо подключает monkeypatch feedparser.parse,
#             чтобы не трогать существующие импорты/команды.
#             Если файл уже существует — НЕ удаляем его содержимое; просто добавляем импорт.
try:
    from . import monkeypatch  # noqa: F401
except Exception:
    # Безопасно игнорируем ошибки, чтобы не падать на импорт-время
    pass
