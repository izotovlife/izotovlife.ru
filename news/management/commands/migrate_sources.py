# backend/news/management/commands/migrate_sources.py
# Назначение: перенос строкового поля source → в модель NewsSource и заполнение source_fk
# Путь: backend/news/management/commands/migrate_sources.py

from django.core.management.base import BaseCommand
from news.models import ImportedNews, NewsSource


class Command(BaseCommand):
    help = "Перенос строковых источников из ImportedNews.source в NewsSource и заполнение source_fk"

    def handle(self, *args, **options):
        migrated = 0
        skipped = 0

        for news in ImportedNews.objects.all():
            if news.source and not news.source_fk:
                source_obj, _ = NewsSource.objects.get_or_create(name=news.source.strip())
                news.source_fk = source_obj
                news.save(update_fields=["source_fk"])
                migrated += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Перенос завершён: обновлено {migrated}, пропущено {skipped}."
        ))
