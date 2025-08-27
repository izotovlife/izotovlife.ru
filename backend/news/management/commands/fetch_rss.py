# ===== ФАЙЛ: backend/news/management/commands/fetch_rss.py =====
# ПУТЬ: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\backend\news\management\commands\fetch_rss.py
# НАЗНАЧЕНИЕ: Загружает новости из RSS-лент во внутреннюю базу.
# ОПИСАНИЕ: Использует библиотеку feedparser; каждая запись сохраняется как News.

import feedparser
from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import News

FEEDS = [
    "https://lenta.ru/rss/news",
]


class Command(BaseCommand):
    help = "Загрузить новости из RSS-лент"

    def handle(self, *args, **options):
        for url in FEEDS:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                News.objects.get_or_create(
                    link=entry.get("link"),
                    defaults={
                        "title": entry.get("title", "No title"),
                        "content": entry.get("summary", ""),
                        "source_type": "rss",
                        "created_at": timezone.now(),
                    },
                )
        self.stdout.write(self.style.SUCCESS("RSS загрузка завершена"))
