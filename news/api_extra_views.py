# Путь: backend/news/api_extra_views.py
# Назначение: API-вьюхи для определения типа новости и редиректа по slug.
# Обновления:
#   ✅ Учитывает field source_fk.
#   ✅ Работает с вариантами slug (с/без "source-" и завершающего "-").
#   ✅ Возвращает корректный seo_url.
#   ✅ Совместим с фронтендом NewsDetailPage.js.

from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.http import require_GET
from .models import Article, ImportedNews


def _slug_variants(slug: str):
    """Возвращает список возможных вариантов slug (с/без source-, с/без завершающего '-')"""
    if not slug:
        return []
    variants = {slug}
    if slug.endswith("-"):
        variants.add(slug.rstrip("-"))
    else:
        variants.add(slug + "-")
    if slug.startswith("source-"):
        variants.add(slug.replace("source-", "", 1))
    return list(variants)


@require_GET
def resolve_news(request, slug):
    """
    Определяет тип новости (article | rss) по slug.
    Возвращает JSON с полями:
    {
        "type": "article" | "rss",
        "slug": "<slug>",
        "category": "<category_slug>",
        "source": "<source_slug>",
        "seo_url": "/news/.../..."
    }
    """
    slug_variants = _slug_variants(slug)

    # ---- Пытаемся найти Article ----
    article = Article.objects.filter(slug__in=slug_variants, status="PUBLISHED").first()
    if article:
        category_slug = (
            article.categories.first().slug if article.categories.exists() else "news"
        )
        return JsonResponse({
            "type": "article",
            "slug": article.slug,
            "category": category_slug,
            "seo_url": f"/news/{category_slug}/{article.slug}/"
        })

    # ---- Пытаемся найти ImportedNews ----
    imported = (
        ImportedNews.objects.filter(slug__in=slug_variants)
        .select_related("source_fk")
        .first()
    )
    if imported:
        source_slug = imported.source_fk.slug if imported.source_fk else "source"
        return JsonResponse({
            "type": "rss",
            "slug": imported.slug,
            "source": source_slug,
            "seo_url": f"/news/source/{source_slug}/{imported.slug}/"
        })

    raise Http404("Новость не найдена")


@require_GET
def by_slug_redirect(request, slug):
    """
    Делает redirect по короткому slug → на правильный API-маршрут.
    """
    slug_variants = _slug_variants(slug)

    article = Article.objects.filter(slug__in=slug_variants, status="PUBLISHED").first()
    if article:
        category_slug = (
            article.categories.first().slug if article.categories.exists() else "news"
        )
        return HttpResponseRedirect(f"/api/news/article/{category_slug}/{article.slug}/")

    imported = (
        ImportedNews.objects.filter(slug__in=slug_variants)
        .select_related("source_fk")
        .first()
    )
    if imported:
        source_slug = imported.source_fk.slug if imported.source_fk else "source"
        return HttpResponseRedirect(f"/api/news/rss/{source_slug}/{imported.slug}/")

    raise Http404("Новость не найдена")
