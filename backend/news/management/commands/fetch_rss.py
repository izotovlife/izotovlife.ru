# ===== ФАЙЛ: backend/news/management/commands/fetch_rss.py =====
# ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\backend\\news\\management\\commands\\fetch_rss.py
# НАЗНАЧЕНИЕ: Загружает новости из популярных RSS-лент Рунета во внутреннюю базу.
# ОПИСАНИЕ: Для каждой записи RSS создаёт или обновляет News и связанные категории.

import feedparser
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from news.models import News, Category

# Подборка популярных новостных RSS-лент
FEEDS = [
    "https://lenta.ru/rss/news",
    "https://tass.ru/rss/v2.xml",
    "https://static.feed.rbc.ru/rbc/logical/footer/news.rss",
    "https://www.kommersant.ru/RSS/news.xml",
]


class Command(BaseCommand):
    help = "Загрузить новости из RSS-лент"

    def handle(self, *args, **options):
        for url in FEEDS:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Определяем категорию
                tag = entry.get("tags", [{}])[0].get("term", "Общее")
                category, _ = Category.objects.get_or_create(
                    name=tag, defaults={"slug": slugify(tag)}
                )

                # Пытаемся найти изображение
                image = ""
                if entry.get("media_content"):
                    image = entry.media_content[0].get("url", "")
                elif entry.get("links"):
                    for link in entry.links:
                        if link.get("type", "").startswith("image"):
                            image = link.get("href", "")
                            break

                News.objects.get_or_create(
                    link=entry.get("link"),
                    defaults={
                        "title": entry.get("title", "No title"),
                        "content": entry.get("summary", ""),
                        "image": image,
                        "category": category,
                        "source_type": "rss",
                        "created_at": timezone.now(),
                    },
                )
        self.stdout.write(self.style.SUCCESS("RSS загрузка завершена"))
