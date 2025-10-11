# Путь: backend/news/migrations/0021_add_search_indexes.py
# Назначение: создаёт полнотекстовые индексы PostgreSQL для ускорения поиска.

from django.db import migrations  # ← импорт должен быть ПЕРЕД классом и без других строк между ними

class Migration(migrations.Migration):
    atomic = False  # ← должно идти ПЕРЕД dependencies, не ниже!

    dependencies = [
        ('news', '0019_newssource_is_active'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_search
                ON news_article USING GIN (
                    to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(content,''))
                );

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_imported_search
                ON news_importednews USING GIN (
                    to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(summary,'') || ' ' || coalesce(content,''))
                );
            """,
            reverse_sql="""
                DROP INDEX IF EXISTS idx_article_search;
                DROP INDEX IF EXISTS idx_imported_search;
            """,
        ),
    ]
