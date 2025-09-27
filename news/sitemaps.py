# news/sitemaps.py
# Назначение: определение карт (sitemap) для различных разделов сайта.
# Эти классы используются в backend/urls.py для генерации sitemap.xml.

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from news.models import Category, Article, ImportedNews

class StaticViewSitemap(Sitemap):
    """Карта для статических страниц (политика, условия и т.п.)."""
    changefreq = "weekly"
    priority = 0.5

    # укажите имена URL-шаблонов для статических страниц вашего проекта
    static_urls = ["home", "about", "privacy", "terms"]

    def items(self):
        return self.static_urls

    def location(self, item):
        return reverse(item)

class CategorySitemap(Sitemap):
    """Карта для категорий новостей."""
    changefreq = "daily"
    priority = 0.6

    def items(self):
        return Category.objects.all().order_by("name")

    def lastmod(self, obj):
        # если в модели Category есть поле updated_at — можно его использовать;
        # иначе можно вернуть None
        return getattr(obj, "updated_at", None)

class ArticleSitemap(Sitemap):
    """Карта для авторских статей."""
    changefreq = "hourly"
    priority = 0.8

    def items(self):
        # выводим только опубликованные статьи с непустым контентом
        return Article.objects.filter(status="PUBLISHED").exclude(content__exact="")

    def lastmod(self, obj):
        return obj.published_at

class ImportedNewsSitemap(Sitemap):
    """Карта для импортированных новостей (RSS)."""
    changefreq = "hourly"
    priority = 0.7

    def items(self):
        # выводим только новости с непустым summary
        return ImportedNews.objects.exclude(summary__exact="")

    def lastmod(self, obj):
        # используем published_at, либо created_at, если published_at отсутствует
        return obj.published_at or obj.created_at
