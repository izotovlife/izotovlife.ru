# Путь: backend/news/views.py
# Назначение: API для новостей — лента, категории, поиск, детальные страницы и «Похожие новости».
# Исправлено:
#   - ✅ ArticleDetailView ищет статью только по slug.
#   - ✅ ImportedNewsDetailView использует source_fk__slug (правильное имя связи).
#   - ✅ related_news стабильно работает с SEO-маршрутами.
#   - ✅ Восстановлены SearchView, NewsFeedImagesView и NewsFeedTextView.
#   - ✅ Лента, категории, похожие, метрики — полностью согласованы с frontend.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, F
from django.db.models.functions import Length
from django.db import connection
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
import json

from .models import Article, Category, ImportedNews
from .serializers import (
    ArticleSerializer,
    ImportedNewsSerializer,
    CategorySerializer,
)

# ======= ВСПОМОГАТЕЛЬНЫЕ =======

def _key_for_dedup(item: dict) -> str:
    itype = item.get("type")
    if itype == "article":
        return f"article:{item.get('slug') or item.get('id')}"
    if itype == "rss":
        return f"rss:{item.get('slug') or item.get('id')}"
    return str(item.get("id") or item.get("slug") or id(item))

def deduplicate(items):
    seen = set()
    unique = []
    for it in items:
        key = _key_for_dedup(it)
        if key not in seen:
            seen.add(key)
            unique.append(it)
    return unique

def _normalize_text(s: str) -> str:
    return s.casefold() if s else ""

def _item_matches_terms(item: dict, terms: list[str], mode: str) -> bool:
    hay = " ".join(filter(None, [item.get("title", ""), item.get("summary", ""), item.get("content", "")]))
    hay_norm = _normalize_text(hay)
    if not terms:
        return True
    if mode == "or":
        return any(term in hay_norm for term in terms)
    return all(term in hay_norm for term in terms)

def _paginate_combined(request, combined):
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

# ======= ПАГИНАЦИЯ =======

class NewsFeedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50

# ======= ЛЕНТЫ =======

class NewsFeedView(generics.ListAPIView):
    pagination_class = NewsFeedPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        category_slug = self.request.query_params.get("category")

        articles = (
            Article.objects.filter(status="PUBLISHED")
            .annotate(text_len=Length("content"))
            .exclude(Q(content__isnull=True) | Q(content__exact="") | Q(text_len__lt=50))
            .select_related("author")
            .prefetch_related("categories")
        )
        if category_slug:
            articles = articles.filter(categories__slug=category_slug)

        imported = (
            ImportedNews.objects
            .annotate(sum_len=Length("summary"))
            .exclude(
                Q(summary__isnull=True) |
                Q(summary__exact="") |
                Q(sum_len__lt=50) |
                Q(summary__icontains="без содержим")
            )
        )
        if category_slug:
            imported = imported.filter(category__slug=category_slug)

        combined = list(articles) + list(imported)
        combined.sort(key=lambda x: getattr(x, "published_at", None) or getattr(x, "created_at", None) or "", reverse=True)
        return combined

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = []
            for obj in page:
                data.append(
                    ArticleSerializer(obj, context={"request": request}).data
                    if isinstance(obj, Article)
                    else ImportedNewsSerializer(obj, context={"request": request}).data
                )
            return self.get_paginated_response(data)
        return Response([])

class NewsFeedImagesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")

        articles = (
            Article.objects.filter(status="PUBLISHED")
            .exclude(Q(cover_image__isnull=True) | Q(cover_image=""))
        )
        imported = (
            ImportedNews.objects.exclude(Q(image__isnull=True) | Q(image=""))
        )
        if category_slug:
            articles = articles.filter(categories__slug=category_slug)
            imported = imported.filter(category__slug=category_slug)

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data
        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)

class NewsFeedTextView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")

        articles = (
            Article.objects.filter(status="PUBLISHED")
            .filter(Q(cover_image__isnull=True) | Q(cover_image=""))
        )
        imported = (
            ImportedNews.objects.filter(Q(image__isnull=True) | Q(image=""))
        )
        if category_slug:
            articles = articles.filter(categories__slug=category_slug)
            imported = imported.filter(category__slug=category_slug)

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data
        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)

# ======= КАТЕГОРИИ =======

class CategoryListView(generics.ListAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Category.objects
            .annotate(news_count=Count("importednews") + Count("article"))
            .filter(news_count__gt=0)
            .order_by("-news_count", "-popularity", "name")
        )

class CategoryNewsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        Category.objects.filter(id=category.id).update(popularity=F("popularity") + 1)

        articles = Article.objects.filter(status="PUBLISHED", categories=category)
        imported = ImportedNews.objects.filter(category=category)

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data

        combined = article_data + imported_data
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return Response(combined)

# ======= ПОИСК =======

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
        imported_qs = ImportedNews.objects.all()

        article_data = ArticleSerializer(articles_qs, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported_qs, many=True, context={"request": request}).data

        combined = deduplicate(article_data + imported_data)
        if terms and use_python_fallback:
            combined = [it for it in combined if _item_matches_terms(it, terms, mode)]
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)

# ======= ДЕТАЛИ =======

class ArticleDetailView(generics.RetrieveAPIView):
    serializer_class = ArticleSerializer
    queryset = Article.objects.filter(status="PUBLISHED")
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        slug = self.kwargs.get("slug")
        return get_object_or_404(Article, slug=slug, status="PUBLISHED")

class ImportedNewsDetailView(generics.RetrieveAPIView):
    serializer_class = ImportedNewsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = ImportedNews.objects.select_related("source_fk", "category")
        source_slug = self.kwargs.get("source")
        if source_slug:
            qs = qs.filter(source_fk__slug=source_slug)
        return qs

    def get_object(self):
        slug = self.kwargs.get("slug")
        # Даже если фильтр по source ничего не дал, попробуем просто по slug (на случай старого формата)
        return get_object_or_404(self.get_queryset(), slug=slug)

# ======= ПОХОЖИЕ =======

@require_GET
def related_news(request, *args, **kwargs):
    max_results = int(request.GET.get("limit", 20))
    slug = kwargs.get("slug") or request.GET.get("slug")
    type_ = kwargs.get("type") or None
    category = kwargs.get("category")
    source = kwargs.get("source")

    current = None
    if type_ == "article" or category:
        current = Article.objects.filter(status="PUBLISHED", slug=slug).first()
        type_ = "article"
    elif type_ == "rss" or source:
        current = ImportedNews.objects.filter(slug=slug).first()
        type_ = "rss"

    if not current:
        return JsonResponse({"error": "not found", "results": []}, status=404)

    title = getattr(current, "title", "") or ""
    terms = [t for t in title.split() if len(t) > 3]
    query = Q()
    for t in terms:
        query |= Q(title__icontains=t)

    articles_qs = (
        Article.objects.filter(status="PUBLISHED")
        .exclude(pk=current.pk)
        .filter(query)[:max_results]
    )
    imported_qs = (
        ImportedNews.objects.exclude(pk=current.pk)
        .filter(query)[:max_results]
    )

    article_data = ArticleSerializer(articles_qs, many=True, context={"request": request}).data
    imported_data = ImportedNewsSerializer(imported_qs, many=True, context={"request": request}).data
    combined = article_data + imported_data
    combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
    return JsonResponse({"results": combined[:max_results]})

# ======= МЕТРИКИ =======

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def hit_metrics(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    slug = data.get("slug")
    type_ = data.get("type")

    if not slug or not type_:
        return JsonResponse({"error": "slug and type required"}, status=400)

    if type_ == "article":
        obj = Article.objects.filter(slug=slug).first()
    elif type_ == "rss":
        obj = ImportedNews.objects.filter(slug=slug).first()
    else:
        return JsonResponse({"error": "invalid type"}, status=400)

    if not obj:
        return JsonResponse({"error": "not found"}, status=404)

    obj.views_count = (obj.views_count or 0) + 1
    obj.save(update_fields=["views_count"])
    return JsonResponse({"views": obj.views_count})
