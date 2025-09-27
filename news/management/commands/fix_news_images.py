# backend/news/management/commands/fix_news_images.py
# Назначение: Проверяет картинки у ImportedNews и Article, если битая или пустая —
# заменяет на дефолтную (/static/default_news.svg).
# Путь: backend/news/management/commands/fix_news_images.py

import requests
from django.core.management.base import BaseCommand
from news.models import ImportedNews, Article

DEFAULT_IMAGE = "/static/default_news.svg"

def is_valid_image(url: str) -> bool:
    """Проверка: ссылка ведет на картинку и доступна."""
    if not url:
        return False
    try:
        r = requests.head(url, timeout=5)
        if r.status_code == 200 and "image" in r.headers.get("Content-Type", ""):
            return True
    except Exception:
        return False
    return False


class Command(BaseCommand):
    help = "Заменяет битые картинки у ImportedNews и Article на дефолтную"

    def handle(self, *args, **options):
        fixed = 0

        # ImportedNews
        for news in ImportedNews.objects.all():
            if not news.image or not is_valid_image(news.image):
                news.image = DEFAULT_IMAGE
                news.save(update_fields=["image"])
                fixed += 1

        # Article
        for article in Article.objects.all():
            url = article.cover_image.url if article.cover_image else ""
            if not url or not is_valid_image(url):
                article.cover_image = DEFAULT_IMAGE
                article.save(update_fields=["cover_image"])
                fixed += 1

        self.stdout.write(self.style.SUCCESS(f"Готово! Исправлено {fixed} новостей"))
