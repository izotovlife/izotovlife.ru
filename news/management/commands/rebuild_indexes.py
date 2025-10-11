# Путь: backend/news/management/commands/rebuild_indexes.py
# Назначение: Django-команда для пересоздания полнотекстовых GIN-индексов в PostgreSQL.
# Поддерживает поля title, content (Article) и summary (ImportedNews).
# Использование: python manage.py rebuild_indexes
# Безопасно для продакшена — CREATE INDEX CONCURRENTLY не блокирует таблицы.

from django.core.management.base import BaseCommand
from django.db import connection

SQL_INDEXES = [
    # --- Авторские статьи ---
    {
        "name": "news_article_title_idx",
        "table": "news_article",
        "vector": "to_tsvector('russian', coalesce(title, ''))",
        "description": "по заголовку статей",
    },
    {
        "name": "news_article_content_idx",
        "table": "news_article",
        "vector": "to_tsvector('russian', coalesce(content, ''))",
        "description": "по содержимому статей",
    },
    # --- Импортированные новости ---
    {
        "name": "news_importednews_title_idx",
        "table": "news_importednews",
        "vector": "to_tsvector('russian', coalesce(title, ''))",
        "description": "по заголовку импортированных новостей",
    },
    {
        "name": "news_importednews_summary_idx",
        "table": "news_importednews",
        "vector": "to_tsvector('russian', coalesce(summary, ''))",
        "description": "по краткому описанию импортированных новостей",
    },
]


class Command(BaseCommand):
    help = "Пересоздаёт полнотекстовые GIN-индексы для моделей Article и ImportedNews (PostgreSQL)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("🔧 Пересоздание полнотекстовых индексов..."))
        with connection.cursor() as cursor:
            for index in SQL_INDEXES:
                name = index["name"]
                table = index["table"]
                vector = index["vector"]
                desc = index["description"]

                self.stdout.write(self.style.WARNING(f"Удаление индекса {name} ({desc})..."))
                cursor.execute(f"DROP INDEX IF EXISTS {name};")

                self.stdout.write(self.style.HTTP_INFO(f"Создание индекса {name} на таблице {table}..."))
                cursor.execute(
                    f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {name} "
                    f"ON {table} USING gin ({vector});"
                )

                self.stdout.write(self.style.SUCCESS(f"✅ Индекс {name} ({desc}) успешно создан."))

        self.stdout.write(self.style.SUCCESS("🎯 Все GIN-индексы успешно пересозданы!"))
