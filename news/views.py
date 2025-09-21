# backend/news/views.py
# Назначение: API для новостей — лента (feed), категории, поиск, детальные страницы.
# Логика: убираем дубликаты до пагинации, корректная бесконечная подгрузка, регистронезависимый поиск.
# Добавлено: категории отдаются только если есть новости (articles или imported).
# Путь: backend/news/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from django.db.models import Q, Count
from django.db import connection
from django.shortcuts import get_object_or_404

from .models import Article, Category, ImportedNews
from .serializers import (
    ArticleSerializer,
    ImportedNewsSerializer,
    CategorySerializer,
)
from .pagination import NewsFeedPagination


# ===== ВСПОМОГАТЕЛЬНОЕ =====

def _key_for_dedup(item: dict) -> str:
    """Формируем ключ для удаления дублей."""
    itype = item.get("type")
    if itype == "article":
        if item.get("slug"):
            return f"article:{item['slug']}"
        if item.get("id"):
            return f"article-id:{item['id']}"
    if itype == "rss":
        if item.get("id"):
            return f"rss:{item['id']}"
        if item.get("source_url"):
            return f"rss-url:{item['source_url']}"
    return str(item.get("id") or item.get("slug") or item.get("source_url") or id(item))


def deduplicate(items):
    """Удаляем дубликаты по ключу."""
    seen = set()
    unique = []
    for it in items:
        k = _key_for_dedup(it)
        if k not in seen:
            seen.add(k)
            unique.append(it)
    return unique


def _normalize_text(s: str) -> str:
    if not s:
        return ""
    try:
        return s.casefold()
    except Exception:
        return s.lower()


def _item_matches_terms(item: dict, terms: list[str], mode: str) -> bool:
    hay = " ".join(filter(None, [
        item.get("title", ""),
        item.get("summary", ""),
        item.get("content", ""),
    ]))
    hay_norm = _normalize_text(hay)
    if not terms:
        return True
    if mode == "or":
        return any(term in hay_norm for term in terms)
    return all(term in hay_norm for term in terms)


def _paginate_combined(request, combined):
    """Пагинация: поддержка limit/offset или DRF-пагинации."""
    limit_raw = request.query_params.get("limit")
    offset_raw = request.query_params.get("offset")
    if limit_raw is not None:
        try:
            limit = max(0, int(limit_raw))
        except ValueError:
            limit = 30
        try:
            offset = max(0, int(offset_raw or 0))
        except ValueError:
            offset = 0
        sliced = combined[offset: offset + limit if limit else None]
        return Response({"results": sliced, "count": len(combined)})

    paginator = NewsFeedPagination()
    page = paginator.paginate_queryset(combined, request)
    return paginator.get_paginated_response(page)


# ============================================================
# Общая лента
# ============================================================

class NewsFeedView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")

        articles = Article.objects.filter(status="PUBLISHED")
        if category_slug:
            articles = articles.filter(categories__slug=category_slug)

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        for a in article_data:
            a["type"] = "article"
            a["image"] = a.get("cover_image") or None

        imported = ImportedNews.objects.all()
        if category_slug:
            imported = imported.filter(category__slug=category_slug)

        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data
        for i in imported_data:
            i["type"] = "rss"
            i["image"] = i.get("image") or None

        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)


# ============================================================
# Фото-новости
# ============================================================

class NewsFeedImagesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")

        articles = Article.objects.filter(status="PUBLISHED")
        if category_slug:
            articles = articles.filter(categories__slug=category_slug)
        articles = articles.exclude(cover_image__isnull=True).exclude(cover_image="")

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        for a in article_data:
            a["type"] = "article"
            a["image"] = a.get("cover_image") or None

        imported = ImportedNews.objects.all()
        if category_slug:
            imported = imported.filter(category__slug=category_slug)
        imported = imported.exclude(image__isnull=True).exclude(image="")

        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data
        for i in imported_data:
            i["type"] = "rss"
            i["image"] = i.get("image") or None

        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)


# ============================================================
# Текстовые новости
# ============================================================

class NewsFeedTextView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")

        articles = Article.objects.filter(status="PUBLISHED")
        if category_slug:
            articles = articles.filter(categories__slug=category_slug)
        articles = articles.filter(Q(cover_image__isnull=True) | Q(cover_image=""))

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        for a in article_data:
            a["type"] = "article"
            a["image"] = None

        imported = ImportedNews.objects.all()
        if category_slug:
            imported = imported.filter(category__slug=category_slug)
        imported = imported.filter(Q(image__isnull=True) | Q(image=""))

        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data
        for i in imported_data:
            i["type"] = "rss"
            i["image"] = None

        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)


# ============================================================
# Категории
# ============================================================

class CategoryListView(generics.ListAPIView):
    """Возвращает только категории, в которых есть новости"""
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Category.objects
            .annotate(news_count=Count("importednews") + Count("article"))
            .filter(news_count__gt=0)
            .order_by("name")
        )


class CategoryNewsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)

        articles = Article.objects.filter(status="PUBLISHED", categories=category)
        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        for a in article_data:
            a["type"] = "article"
            a["image"] = a.get("cover_image") or None

        imported = ImportedNews.objects.filter(category=category)
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data
        for i in imported_data:
            i["type"] = "rss"
            i["image"] = i.get("image") or None

        combined = article_data + imported_data
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return Response(combined)


# ============================================================
# Поиск
# ============================================================

class SearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        raw_q = request.query_params.get("q", "").strip()
        mode = request.query_params.get("mode", "and").lower()
        if not raw_q:
            return Response({"results": [], "count": 0})

        terms = [_normalize_text(t) for t in raw_q.split() if t]

        vendor = connection.vendor
        use_python_fallback = (vendor == "sqlite")

        articles_qs = Article.objects.filter(status="PUBLISHED")
        if terms and not use_python_fallback:
            qa = Q()
            for term in terms:
                clause = Q(title__icontains=term) | Q(content__icontains=term)
                qa = (qa | clause) if mode == "or" else (qa & clause)
            articles_qs = articles_qs.filter(qa).distinct()

        imported_qs = ImportedNews.objects.all()
        if terms and not use_python_fallback:
            qi = Q()
            for term in terms:
                clause = Q(title__icontains=term) | Q(summary__icontains=term)
                qi = (qi | clause) if mode == "or" else (qi & clause)
            imported_qs = imported_qs.filter(qi).distinct()

        article_data = ArticleSerializer(articles_qs, many=True, context={"request": request}).data
        for a in article_data:
            a["type"] = "article"
            a["image"] = a.get("cover_image") or None

        imported_data = ImportedNewsSerializer(imported_qs, many=True, context={"request": request}).data
        for i in imported_data:
            i["type"] = "rss"
            i["image"] = i.get("image") or None

        combined = deduplicate(article_data + imported_data)

        if terms and use_python_fallback:
            combined = [it for it in combined if _item_matches_terms(it, terms, mode)]

        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)


# ============================================================
# Детальные страницы
# ============================================================

class ArticleDetailView(generics.RetrieveAPIView):
    queryset = Article.objects.filter(status="PUBLISHED")
    serializer_class = ArticleSerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]


class ImportedNewsDetailView(generics.RetrieveAPIView):
    queryset = ImportedNews.objects.all()
    serializer_class = ImportedNewsSerializer
    lookup_field = "id"
    permission_classes = [permissions.AllowAny]
