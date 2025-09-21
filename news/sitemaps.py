# backend/news/sitemaps.py
# Назначение: генерация sitemap.xml для статей, RSS-новостей и категорий с датами обновлений.
# Путь: backend/news/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Article, ImportedNews, Category


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return ["feed"]

    def location(self, item):
        if item == "feed":
            return reverse("news:news_feed")


class CategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return f"/category/{obj.slug}/"


class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Article.objects.filter(status="PUBLISHED")

    def location(self, obj):
        return f"/article/{obj.slug}/"

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None) or getattr(obj, "published_at", None)


class ImportedNewsSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return ImportedNews.objects.all()

    def location(self, obj):
        return f"/news/{obj.id}/"

    def lastmod(self, obj):
        return getattr(obj, "published_at", None) or getattr(obj, "created_at", None)
