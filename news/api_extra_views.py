# Путь: backend/news/api_extra_views.py
# Назначение: API-вьюхи для определения типа новости и редиректа по slug.
# Обновления:
#   ✅ Добавлено логирование для отладки.
#   ✅ Обработаны slug-варианты безопасно (без ложных совпадений).
#   ✅ Возвращает корректные seo_url и не ломает категории.
#   ✅ Старый код сохранён в комментариях.
#   ✅ Совместим с фронтендом NewsDetailPage.js.

from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.http import require_GET
from .models import Article, ImportedNews


# ===========================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ
# ===========================================================

def _slug_variants(slug: str):
    """
    Возвращает список возможных вариантов slug (с/без source-, с/без завершающего '-').
    Используется для поиска новостей по нестандартным slug.
    """
    if not slug:
        return []
    variants = {slug}
    if slug.endswith("-"):
        variants.add(slug.rstrip("-"))
    else:
        variants.add(slug + "-")
    if slug.startswith("source-"):
        variants.add(slug.replace("source-", "", 1))
    # Убираем пустые строки
    variants = {v for v in variants if v}
    return list(variants)


# ===========================================================
# ОПРЕДЕЛЕНИЕ ТИПА НОВОСТИ
# ===========================================================

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
    print(f"[resolve_news] Проверяем slug={slug}, варианты={slug_variants}")

    # ---- Пытаемся найти Article ----
    article = Article.objects.filter(slug__in=slug_variants, status="PUBLISHED").first()
    if article:
        category_slug = (
            article.categories.first().slug if article.categories.exists() else "news"
        )
        seo_url = f"/news/{category_slug}/{article.slug}/"
        print(f"[resolve_news] ✅ Найден Article: {seo_url}")
        return JsonResponse({
            "type": "article",
            "slug": article.slug,
            "category": category_slug,
            "source": None,
            "seo_url": seo_url
        })

    # ---- Пытаемся найти ImportedNews ----
    imported = (
        ImportedNews.objects.filter(slug__in=slug_variants)
        .select_related("source_fk", "category")
        .first()
    )
    if imported:
        source_slug = imported.source_fk.slug if imported.source_fk else "source"
        seo_url = f"/news/source/{source_slug}/{imported.slug}/"
        print(f"[resolve_news] ✅ Найден ImportedNews: {seo_url}")
        return JsonResponse({
            "type": "rss",
            "slug": imported.slug,
            "category": imported.category.slug if imported.category else None,
            "source": source_slug,
            "seo_url": seo_url
        })

    # ---- Если ничего не найдено ----
    print(f"[resolve_news] ⚠️ Ничего не найдено по slug={slug}")
    raise Http404("Новость не найдена")


# ===========================================================
# РЕДИРЕКТ ПО SLUG → НА API URL
# ===========================================================

@require_GET
def by_slug_redirect(request, slug):
    """
    Делает redirect по короткому slug → на правильный API-маршрут.
    Пример:
      /api/news/by-slug/ekonomika-rossii → /api/news/article/ekonomika/ekonomika-rossii/
      /api/news/by-slug/source-kommersant-123 → /api/news/rss/kommersant/source-kommersant-123/
    """
    slug_variants = _slug_variants(slug)
    print(f"[by_slug_redirect] slug={slug}, варианты={slug_variants}")

    # ---- Article ----
    article = Article.objects.filter(slug__in=slug_variants, status="PUBLISHED").first()
    if article:
        category_slug = (
            article.categories.first().slug if article.categories.exists() else "news"
        )
        target = f"/api/news/article/{category_slug}/{article.slug}/"
        print(f"[by_slug_redirect] ✅ Перенаправляем на Article: {target}")
        return HttpResponseRedirect(target)

    # ---- ImportedNews ----
    imported = (
        ImportedNews.objects.filter(slug__in=slug_variants)
        .select_related("source_fk")
        .first()
    )
    if imported:
        source_slug = imported.source_fk.slug if imported.source_fk else "source"
        target = f"/api/news/rss/{source_slug}/{imported.slug}/"
        print(f"[by_slug_redirect] ✅ Перенаправляем на ImportedNews: {target}")
        return HttpResponseRedirect(target)

    print(f"[by_slug_redirect] ❌ Не удалось определить тип по slug={slug}")
    raise Http404("Новость не найдена")


# ===========================================================
# СТАРЫЙ ВАРИАНТ (оставлен для истории)
# ===========================================================
"""
@require_GET
def resolve_news(request, slug):
    slug_variants = _slug_variants(slug)
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
"""

# ⛔ Отключено, потому что не возвращало "source=None" для Article (вызвало ошибку на фронте)
# ⛔ Также не выводило category в RSS и не логировало поведение для отладки.
