# backend/news/management/commands/list_slugs.py
# Назначение: Выводит список всех Article и ImportedNews с их slug для проверки SEO-адресов.

from django.core.management.base import BaseCommand
from news.models import Article, ImportedNews

class Command(BaseCommand):
    help = "Список slug для Article и ImportedNews"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Article (статьи) ==="))
        for art in Article.objects.all().order_by("-created_at"):
            self.stdout.write(f"  /news/{(art.categories.first().slug if art.categories.exists() else 'news')}/{art.slug}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== ImportedNews (импортированные) ==="))
        for rss in ImportedNews.objects.all().order_by("-created_at"):
            src_slug = rss.source_fk.slug if rss.source_fk else "source"
            self.stdout.write(f"  /news/{src_slug}/{rss.slug}")
