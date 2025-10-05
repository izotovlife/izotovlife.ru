# backend/news/api_extra_views.py
# Назначение: Дополнительные API-вьюхи (резолвер, редиректы, быстрый автопоиск)
# ✅ Молниеносный /api/news/autocomplete/
# ✅ Работает с Article и ImportedNews
# ✅ Возвращает title, image, source_name, seo_url
# ✅ Полностью совместим с SearchAutocomplete.jsx

from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.views.decorators.http import require_GET
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Article, ImportedNews


# ----------- РЕЗОЛВЕР -----------

def _slug_variants(slug: str):
    if not slug:
        return []
    variants = {slug}
    # допускаем «хвост» дефиса и его отсутствие
    if slug.endswith("-"):
        variants.add(slug.rstrip("-"))
    else:
        variants.add(slug + "-")
    # допускаем снятие префикса source-
    if slug.startswith("source-"):
        variants.add(slug.replace("source-", "", 1))
    return list(variants)


@require_GET
def resolve_news(request, slug):
    slug_variants = _slug_variants(slug)

    # Article
    article = Article.objects.filter(slug__in=slug_variants, status="PUBLISHED").first()
    if article:
        cat = article.categories.first()
        category_slug = cat.slug if cat else "news"
        return JsonResponse({
            "type": "article",
            "slug": article.slug,
            "category": category_slug,
            "seo_url": f"/news/{category_slug}/{article.slug}/",
        })

    # Imported (RSS)
    imported = ImportedNews.objects.filter(slug__in=slug_variants).select_related("source_fk").first()
    if imported:
        source_slug = imported.source_fk.slug if imported.source_fk else "source"
        return JsonResponse({
            "type": "rss",
            "slug": imported.slug,
            "source": source_slug,
            "seo_url": f"/news/source/{source_slug}/{imported.slug}/",
        })

    raise Http404("Новость не найдена")


@require_GET
def by_slug_redirect(request, slug):
    slug_variants = _slug_variants(slug)

    # Article
    article = Article.objects.filter(slug__in=slug_variants, status="PUBLISHED").first()
    if article:
        cat = article.categories.first()
        category_slug = cat.slug if cat else "news"
        return HttpResponseRedirect(f"/api/news/article/{category_slug}/{article.slug}/")

    # Imported (RSS) — ВАЖНО: сегмент source/ в URL обязателен!
    imported = ImportedNews.objects.filter(slug__in=slug_variants).select_related("source_fk").first()
    if imported:
        source_slug = imported.source_fk.slug if imported.source_fk else "source"
        return HttpResponseRedirect(f"/api/news/rss/source/{source_slug}/{imported.slug}/")

    raise Http404("Новость не найдена")


# ----------- ⚡ БЫСТРЫЙ АВТОПОИСК -----------

@api_view(["GET"])
def autocomplete_news(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return Response({"results": []})

    limit = int(request.GET.get("limit", 8))
    query = Q(title__icontains=q)

    # Только нужные поля (молниеносный запрос)
    articles = (
        Article.objects.filter(query, status="PUBLISHED")
        .only("id", "title", "slug", "image")
        .prefetch_related("categories")[:limit]
    )

    imported = (
        ImportedNews.objects.filter(query)
        .select_related("source_fk")[:limit]
    )

    results = []

    for n in articles:
        cat = n.categories.first()
        category_slug = cat.slug if cat else "news"
        results.append({
            "id": n.id,
            "title": n.title,
            "image": getattr(n, "image", None),
            "seo_url": f"/news/{category_slug}/{n.slug}/",
            "source_name": cat.name if cat else "Статья",
        })

    for n in imported:
        source_slug = n.source_fk.slug if n.source_fk else "source"
        results.append({
            "id": n.id,
            "title": n.title,
            "image": getattr(n, "image", None),
            "seo_url": f"/news/source/{source_slug}/{n.slug}/",
            "source_name": n.source_fk.name if n.source_fk else "Источник",
        })

    return Response({"results": results[:limit]})
