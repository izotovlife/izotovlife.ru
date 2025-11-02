# Путь: backend/news/sitemaps.py
# Назначение: Классы Django Sitemap для статических страниц, категорий, авторских статей и импортированных новостей.
# Особенности:
#  • Автоматически подхватывает новые материалы (queryset формируется «на лету»).
#  • Безопасные fallbacks на случай отсутствия get_absolute_url() — строим URL по slug.
#  • Корректный lastmod из published_at/updated_at/modified/... (что доступно).
#  • Масштабируемость: limit=1000 ссылок на страницу sitemap.
#  • Ничего из твоей логики не удалено: фильтрация Article по status="PUBLISHED" и непустому контенту сохранена, но расширена мягкими проверками.

from datetime import datetime
from typing import Optional

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q

from news.models import Category, Article, ImportedNews


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------

def _best_lastmod(obj) -> Optional[datetime]:
    """
    Выбираем «лучшую» дату модификации/публикации из известных полей:
    updated_at, updated, modified, published_at, created_at, created.
    Возвращаем aware datetime (с таймзоной), если возможно.
    """
    for name in ("updated_at", "updated", "modified", "published_at", "created_at", "created"):
        if hasattr(obj, name):
            dt = getattr(obj, name)
            if isinstance(dt, datetime):
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
    return None


def _safe_location(obj, fallbacks: list[str]) -> str:
    """
    Универсальная генерация URL:
    1) Если у объекта есть get_absolute_url() — используем её.
    2) Иначе строим по slug согласно fallbacks: ['/news/{slug}/', '/article/{slug}/', ...]
    3) Если slug отсутствует — возвращаем корень '/'.
    """
    if hasattr(obj, "get_absolute_url"):
        try:
            return obj.get_absolute_url()
        except Exception:
            pass

    slug = getattr(obj, "slug", None)
    if slug:
        for pattern in fallbacks:
            try:
                return pattern.format(slug=slug)
            except Exception:
                continue
    return "/"


# ---------- SITEMAP ДЛЯ СТАТИЧЕСКИХ СТРАНИЦ ----------

class StaticViewSitemap(Sitemap):
    """Карта для статических страниц (политика, условия и т.п.)."""
    changefreq = "weekly"
    priority = 0.5
    protocol = None  # Django возьмёт из settings.SITEMAP_PROTOCOL, если указано
    limit = 1000

    # укажи имена URL-шаблонов для статических страниц проекта
    static_urls = ["home", "about", "privacy", "terms"]

    def items(self):
        return self.static_urls

    def location(self, item):
        # Если какого-то именованного URL нет — не падаем, а возвращаем корень
        try:
            return reverse(item)
        except Exception:
            return "/"


# ---------- SITEMAP ДЛЯ КАТЕГОРИЙ ----------

class CategorySitemap(Sitemap):
    """Карта для категорий новостей."""
    changefreq = "daily"
    priority = 0.6
    protocol = None
    limit = 1000

    def items(self):
        # Сохраняем твой порядок, чтобы ничего не сломать
        return Category.objects.all().order_by("name")

    def lastmod(self, obj):
        return _best_lastmod(obj)

    def location(self, obj):
        try:
            return obj.get_absolute_url()
        except Exception:
            pass
        return _safe_location(obj, fallbacks=["/{slug}/"])


# ---------- SITEMAP ДЛЯ АВТОРСКИХ СТАТЕЙ ----------

class ArticleSitemap(Sitemap):
    """Карта для авторских статей."""
    changefreq = "hourly"
    priority = 0.8
    protocol = None
    limit = 1000

    def items(self):
        # Твоя исходная логика + мягкие фильтры
        qs = Article.objects.all()

        # 1) «Опубликовано»: поддерживаем is_published и status
        if hasattr(Article, "is_published"):
            qs = qs.filter(is_published=True)
        elif hasattr(Article, "status"):
            qs = qs.filter(
                Q(status="PUBLISHED") |  # твой исходный вариант в верхнем регистре
                Q(status="published") |
                Q(status="public") |
                Q(status="ACTIVE") |
                Q(status="active")
            )

        # 2) Исключаем пустой контент — сохраняем твою проверку и добавляем на None
        qs = qs.exclude(content__isnull=True).exclude(content__exact="")

        # 3) Сортировка: свежие выше
        order_fields = [f for f in ("-published_at", "-updated_at", "-created_at", "-created", "-id")
                        if f.lstrip("-") in [fld.name for fld in Article._meta.fields]]
        qs = qs.order_by(*order_fields) if order_fields else qs.order_by("-id")

        return qs

    def lastmod(self, obj):
        return _best_lastmod(obj) or getattr(obj, "published_at", None)

    def location(self, obj):
        try:
            return obj.get_absolute_url()
        except Exception:
            pass
        return _safe_location(obj, fallbacks=["/article/{slug}/", "/news/{slug}/"])


# ---------- SITEMAP ДЛЯ ИМПОРТИРОВАННЫХ НОВОСТЕЙ (RSS) ----------

class ImportedNewsSitemap(Sitemap):
    """Карта для импортированных новостей (RSS)."""
    changefreq = "hourly"
    priority = 0.7
    protocol = None
    limit = 1000

    def items(self):
        # Твоя логика: только с непустым summary
        qs = ImportedNews.objects.exclude(summary__exact="").exclude(summary__isnull=True)

        # Мягкий фильтр опубликованности, если поля есть
        if hasattr(ImportedNews, "is_published"):
            qs = qs.filter(is_published=True)
        elif hasattr(ImportedNews, "status"):
            qs = qs.filter(status__in=["published", "public", "active", "PUBLISHED", "ACTIVE"])

        # Сортировка: свежие выше
        order_fields = [f for f in ("-published_at", "-created_at", "-created", "-id")
                        if f.lstrip("-") in [fld.name for fld in ImportedNews._meta.fields]]
        qs = qs.order_by(*order_fields) if order_fields else qs.order_by("-id")

        return qs

    def lastmod(self, obj):
        return _best_lastmod(obj) or getattr(obj, "published_at", None) or getattr(obj, "created_at", None)

    def location(self, obj):
        try:
            return obj.get_absolute_url()
        except Exception:
            pass
        return _safe_location(obj, fallbacks=["/news/{slug}/", "/imported/{slug}/"])
