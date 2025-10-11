# Путь: backend/news/views.py
# Назначение: API для новостей — лента, категории, поиск, детальные страницы и «Похожие новости».
# Исправлено:
#   ✅ ArticleDetailView ищет статью только по slug.
#   ✅ ImportedNewsDetailView теперь корректно работает с /news/source/<source>/<slug>/.
#   ✅ related_news различает category и source и не даёт 404.
#   ✅ Восстановлены SearchView, NewsFeedImagesView и NewsFeedTextView.
#   ✅ Добавлен SmartSearchView (GIN-поиск PostgreSQL).
#   ✅ Добавлен HitMetricsView (фикс ошибки 405).
#   ✅ CategoryNewsView работает без AssertionError.
#   ✅ Полностью совместим с frontend/src/Api.js (все маршруты /api/news/...).

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q, Count, F
from django.db.models.functions import Length
from django.db import connection
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
import json

from .models import Article, Category, ImportedNews
from .serializers import ArticleSerializer, ImportedNewsSerializer, CategorySerializer

# ===========================================================
# ВСПОМОГАТЕЛЬНЫЕ
# ===========================================================

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
        return Response({"results": sliced, "items": sliced, "count": len(combined)})
    paginator = NewsFeedPagination()
    page = paginator.paginate_queryset(combined, request)
    resp = paginator.get_paginated_response(page)
    data = resp.data
    if "results" in data and "items" not in data:
        data["items"] = data["results"]
    return resp

# ===========================================================
# ПАГИНАЦИЯ
# ===========================================================

class NewsFeedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50

# ===========================================================
# ЛЕНТЫ
# ===========================================================

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
            .exclude(Q(summary__isnull=True) | Q(summary__exact="") | Q(sum_len__lt=50))
        )
        if category_slug:
            imported = imported.filter(category__slug=category_slug)

        combined = list(articles) + list(imported)
        combined.sort(
            key=lambda x: getattr(x, "published_at", None) or getattr(x, "created_at", None) or "",
            reverse=True,
        )
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
        articles = Article.objects.filter(status="PUBLISHED").exclude(Q(cover_image__isnull=True) | Q(cover_image=""))
        imported = ImportedNews.objects.exclude(Q(image__isnull=True) | Q(image=""))
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
        articles = Article.objects.filter(status="PUBLISHED").filter(Q(cover_image__isnull=True) | Q(cover_image=""))
        imported = ImportedNews.objects.filter(Q(image__isnull=True) | Q(image=""))
        if category_slug:
            articles = articles.filter(categories__slug=category_slug)
            imported = imported.filter(category__slug=category_slug)
        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data
        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)

# ===========================================================
# КАТЕГОРИИ
# ===========================================================

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

# ===========================================================
# НОВОСТИ КАТЕГОРИИ
# ===========================================================

class CategoryNewsView(APIView):
    """
    Эндпоинт: GET /api/news/category/<slug>/
    Возвращает объединённую ленту Article + ImportedNews для выбранной категории.
    Поддерживает пагинацию через NewsFeedPagination.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        print(f"[CategoryNewsView] Запрошена категория: {slug}")
        category = get_object_or_404(Category, slug=slug)
        Category.objects.filter(id=category.id).update(popularity=F("popularity") + 1)
        articles = Article.objects.filter(status="PUBLISHED", categories=category)
        imported = ImportedNews.objects.filter(category=category)
        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data
        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        paginator = NewsFeedPagination()
        page = paginator.paginate_queryset(combined, request)
        if page is not None:
            return paginator.get_paginated_response(page)
        return Response({"results": combined, "count": len(combined)})

# ===========================================================
# ПОИСК
# ===========================================================

class SearchView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        raw_q = request.query_params.get("q", "").strip()
        if not raw_q:
            return Response({"results": [], "count": 0})
        vendor = connection.vendor
        is_pg = vendor == "postgresql"
        article_qs = Article.objects.filter(status="PUBLISHED")
        imported_qs = ImportedNews.objects.all()
        if is_pg:
            from django.contrib.postgres.search import SearchQuery
            raw_query = SearchQuery(raw_q, search_type="websearch", config="russian")
            article_qs = article_qs.extra(
                where=["to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(content,'')) @@ plainto_tsquery('russian', %s)"],
                params=[raw_q]
            )
            imported_qs = imported_qs.extra(
                where=["to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(summary,'')) @@ plainto_tsquery('russian', %s)"],
                params=[raw_q]
            )
        article_data = ArticleSerializer(article_qs, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported_qs, many=True, context={"request": request}).data
        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)

# ===========================================================
# УМНЫЙ ПОИСК (GIN)
# ===========================================================

from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

class SmartSearchViewEnhanced(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"results": [], "count": 0})
        vendor = connection.vendor
        is_pg = vendor == "postgresql"
        if is_pg:
            query = SearchQuery(q, search_type="websearch", config="russian")
            article_qs = (
                Article.objects.filter(status="PUBLISHED")
                .annotate(rank=SearchRank(SearchVector("title", "content"), query))
                .filter(rank__gte=0.1)
                .order_by("-rank")[:50]
            )
            imported_qs = (
                ImportedNews.objects
                .annotate(rank=SearchRank(SearchVector("title", "summary"), query))
                .filter(rank__gte=0.1)
                .order_by("-rank")[:50]
            )
        else:
            article_qs = Article.objects.filter(status="PUBLISHED", title__icontains=q)
            imported_qs = ImportedNews.objects.filter(title__icontains=q)
        article_data = ArticleSerializer(article_qs, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported_qs, many=True, context={"request": request}).data
        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)

# ===========================================================
# ДЕТАЛИ
# ===========================================================

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
        source = self.kwargs.get("source")
        if source:
            qs = qs.filter(source_fk__slug=source)
        return qs

    def get_object(self):
        slug = self.kwargs.get("slug")
        return get_object_or_404(self.get_queryset(), slug=slug)

# ===========================================================
# ПОХОЖИЕ
# ===========================================================

@require_GET
def related_news(request, *args, **kwargs):
    """
    Возвращает похожие статьи или импортированные новости.
    Работает с /news/<category>/<slug>/related/ и /news/source/<source>/<slug>/related/.
    """
    max_results = int(request.GET.get("limit", 20))
    slug = kwargs.get("slug") or request.GET.get("slug")
    category = kwargs.get("category")
    source = kwargs.get("source")
    type_ = kwargs.get("type")

    current = None
    if source:
        current = ImportedNews.objects.filter(source_fk__slug=source, slug=slug).first()
        type_ = "rss"
    elif category:
        current = Article.objects.filter(status="PUBLISHED", categories__slug=category, slug=slug).first()
        type_ = "article"
    else:
        current = Article.objects.filter(slug=slug).first() or ImportedNews.objects.filter(slug=slug).first()
        type_ = "rss" if isinstance(current, ImportedNews) else "article"

    if not current:
        return JsonResponse({"error": "not found", "results": []}, status=404)

    title = getattr(current, "title", "") or ""
    terms = [t for t in title.split() if len(t) > 3]
    query = Q()
    for t in terms:
        query |= Q(title__icontains=t)

    if type_ == "article":
        qs = Article.objects.filter(status="PUBLISHED").exclude(pk=current.pk).filter(query)[:max_results]
        data = ArticleSerializer(qs, many=True, context={"request": request}).data
    else:
        qs = ImportedNews.objects.filter(source_fk=current.source_fk).exclude(pk=current.pk).filter(query)[:max_results]
        data = ImportedNewsSerializer(qs, many=True, context={"request": request}).data

    data.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
    return JsonResponse({"results": data[:max_results]})

# ===========================================================
# МЕТРИКИ (фикс 405)
# ===========================================================

# ===========================================================
# МЕТРИКИ (исправлено: поддержка ImportedNews без source)
# ===========================================================

class HitMetricsView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            slug = data.get("slug", "").strip()
            if not slug:
                return Response({"error": "slug required"}, status=status.HTTP_400_BAD_REQUEST)

            # 1. Пробуем Article
            news_obj = Article.objects.filter(slug=slug).first()

            # 2. Если не найдено — ищем ImportedNews
            if not news_obj:
                news_obj = ImportedNews.objects.filter(slug=slug).first()

            if not news_obj:
                return Response(
                    {"error": f"Новость '{slug}' не найдена"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 3. Инкремент просмотров
            news_obj.views_count = (news_obj.views_count or 0) + 1
            news_obj.save(update_fields=["views_count"])

            return Response(
                {"message": "ok", "views_count": news_obj.views_count},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ===========================================================
# УНИВЕРСАЛЬНЫЕ ДЕТАЛЬНЫЕ ВЬЮХИ ДЛЯ /news/<slug>/ и /news/<slug>/related/
# ===========================================================

from rest_framework.generics import RetrieveAPIView

class UniversalNewsDetailView(RetrieveAPIView):
    """
    Универсальный SEO-friendly endpoint для /api/news/<slug>/
    Возвращает Article или ImportedNews по slug.
    """
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        slug = kwargs.get("slug")
        article = Article.objects.filter(slug=slug, status="PUBLISHED").first()
        if article:
            data = ArticleSerializer(article, context={"request": request}).data
            data["type"] = "article"
            return Response(data)

        imported = ImportedNews.objects.filter(slug=slug).first()
        if imported:
            data = ImportedNewsSerializer(imported, context={"request": request}).data
            data["type"] = "rss"
            return Response(data)

        return Response({"detail": "Not found"}, status=404)


class RelatedNewsViewUniversal(APIView):
    """
    Эндпоинт: GET /api/news/<slug>/related/
    Похожие новости без категории и источника в пути.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        current = (
            Article.objects.filter(slug=slug, status="PUBLISHED").first()
            or ImportedNews.objects.filter(slug=slug).first()
        )
        if not current:
            return Response({"results": [], "error": "not found"}, status=404)

        title = getattr(current, "title", "") or ""
        terms = [t for t in title.split() if len(t) > 3]
        query = Q()
        for t in terms:
            query |= Q(title__icontains=t)

        if isinstance(current, Article):
            qs = (
                Article.objects.filter(status="PUBLISHED")
                .exclude(pk=current.pk)
                .filter(query)
                .order_by("-published_at")[:20]
            )
            data = ArticleSerializer(qs, many=True, context={"request": request}).data
        else:
            qs = (
                ImportedNews.objects.exclude(pk=current.pk)
                .filter(query)
                .order_by("-published_at")[:20]
            )
            data = ImportedNewsSerializer(qs, many=True, context={"request": request}).data

        return Response({"results": data})
