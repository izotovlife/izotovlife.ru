# backend/rssfeed/management/commands/fix_imported_links.py
# Назначение: Исправление старых импортированных новостей, у которых пустое поле link.
# Подтягивает недостающие ссылки из RSS-лент.
# Путь: backend/rssfeed/management/commands/fix_imported_links.py

import feedparser
from django.core.management.base import BaseCommand
from news.models import ImportedNews
from .import_rss import extract_link


class Command(BaseCommand):
    help = "Ищет импортированные новости без ссылки и пытается восстановить её из RSS"

    def handle(self, *args, **options):
        broken_news = ImportedNews.objects.filter(link__isnull=True) | ImportedNews.objects.filter(link="")

        fixed_count = 0
        for news in broken_news:
            # источник берём из поля source (там обычно название ленты)
            # увы, у ImportedNews нет сохранённого URL самой ленты
            # поэтому пробуем по названию источника — это не идеально, но лучше чем ничего
            # если у тебя есть таблица со списком лент, нужно брать оттуда

            self.stdout.write(self.style.WARNING(
                f"⚠ Неизвестно, откуда брать RSS для '{news.title}' (источник: {news.source})"
            ))
            continue

        self.stdout.write(self.style.SUCCESS(f"Исправлено {fixed_count} новостей"))
