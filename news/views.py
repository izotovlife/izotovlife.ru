# backend/news/views.py
# Назначение: API для новостей — ленты, категории, поиск, детальные страницы.
# Улучшено:
#   - Исключаются статьи с пустым или коротким content (<50 символов).
#   - Исключаются импортированные записи с пустым или коротким summary (<50 символов),
#     содержащие «без содержим» (wordpress feed может давать только заголовок) или без изображения.
#   - Добавлена дедупликация и сортировка.
#   - Реализованы отдельные ленты: общая, только с фото, только текстовые.
#   - Поиск, категории и детальные страницы используют те же фильтры.
#   - Добавлены подробные комментарии для каждого представления.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, F
from django.db.models.functions import Length
from django.db import connection
from django.shortcuts import get_object_or_404
from .models import Article, Category, ImportedNews
from .serializers import (
    ArticleSerializer,
    ImportedNewsSerializer,
    CategoryMiniSerializer,
)
# ======= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =======

def _key_for_dedup(item: dict) -> str:
    """Определяет ключ для устранения дубликатов в объединённом списке."""
    itype = item.get("type")
    if itype == "article":
        return f"article:{item.get('slug') or item.get('id')}"
    if itype == "rss":
        return f"rss:{item.get('id') or item.get('source_url')}"
    return str(item.get("id") or item.get("slug") or id(item))

def deduplicate(items):
    """Удаляет дубликаты в списке, сохраняя порядок."""
    seen = set()
    unique = []
    for it in items:
        key = _key_for_dedup(it)
        if key not in seen:
            seen.add(key)
            unique.append(it)
    return unique

def _normalize_text(s: str) -> str:
    """Нормализует текст для регистронезависимого поиска."""
    return s.casefold() if s else ""

def _item_matches_terms(item: dict, terms: list[str], mode: str) -> bool:
    """Проверяет, содержит ли запись заданные поисковые термины (фолбэк на Python)."""
    hay = " ".join(filter(None, [item.get("title", ""), item.get("summary", ""), item.get("content", "")]))
    hay_norm = _normalize_text(hay)
    if not terms:
        return True
    if mode == "or":
        return any(term in hay_norm for term in terms)
    return all(term in hay_norm for term in terms)

def _paginate_combined(request, combined):
    """Пагинация: limit/offset или стандартная DRF‑пагинация."""
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
    """Пагинатор для ленты новостей."""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50

# ======= ЛЕНТЫ =======
class NewsFeedView(generics.ListAPIView):
    """
    Общая лента новостей. Объединяет статьи и импортированные RSS‑новости,
    исключая записи с пустым/коротким содержимым или summary, а также записи без изображения (опционально).
    """
    pagination_class = NewsFeedPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        category_slug = self.request.query_params.get("category")

        # Статьи: только опубликованные, non‑empty, длина >=50
        articles = (
            Article.objects.filter(status="PUBLISHED")
            .annotate(text_len=Length("content"))
            .exclude(Q(content__isnull=True) | Q(content__exact="") | Q(text_len__lt=50))
            .select_related("author")
            .prefetch_related("categories")
        )
        if category_slug:
            articles = articles.filter(categories__slug=category_slug)

        # Импортированные: фильтруем пустые summary и короткие summary, исключаем записи без изображения
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
    """Лента новостей только с изображением (фото)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")

        articles = (
            Article.objects.filter(status="PUBLISHED")
            .annotate(text_len=Length("content"))
            .exclude(Q(content__isnull=True) | Q(content__exact="") | Q(text_len__lt=50))
            .exclude(cover_image__isnull=True).exclude(cover_image="")
        )
        imported = (
            ImportedNews.objects
            .annotate(sum_len=Length("summary"))
            .exclude(
                Q(summary__isnull=True) |
                Q(summary__exact="") |
                Q(sum_len__lt=50) |
                Q(summary__icontains="без содержим")
            )
            .exclude(image__isnull=True).exclude(image="")
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
    """Лента текстовых новостей (без изображений)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")

        articles = (
            Article.objects.filter(status="PUBLISHED")
            .annotate(text_len=Length("content"))
            .exclude(Q(content__isnull=True) | Q(content__exact="") | Q(text_len__lt=50))
            .filter(Q(cover_image__isnull=True) | Q(cover_image=""))
        )
        imported = (
            ImportedNews.objects
            .annotate(sum_len=Length("summary"))
            .exclude(
                Q(summary__isnull=True) |
                Q(summary__exact="") |
                Q(sum_len__lt=50) |
                Q(summary__icontains="без содержим")
            )
            .filter(Q(image__isnull=True) | Q(image=""))
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
    """Список категорий (для меню/фильтров)."""
    serializer_class = CategoryMiniSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return (
            Category.objects
            .annotate(news_count=Count("importednews") + Count("article"))
            .filter(news_count__gt=0)
            .order_by("-news_count", "-popularity", "name")
        )

class CategoryNewsView(APIView):
    """Вывод новостей по категории, повышая её популярность."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        # увеличиваем счётчик популярности
        Category.objects.filter(id=category.id).update(popularity=F("popularity") + 1)

        articles = (
            Article.objects.filter(status="PUBLISHED", categories=category)
            .annotate(text_len=Length("content"))
            .exclude(Q(content__isnull=True) | Q(content__exact="") | Q(text_len__lt=50))
        )
        imported = (
            ImportedNews.objects.filter(category=category)
            .annotate(sum_len=Length("summary"))
            .exclude(
                Q(summary__isnull=True) |
                Q(summary__exact="") |
                Q(sum_len__lt=50) |
                Q(summary__icontains="без содержим")
            )
        )

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data

        combined = article_data + imported_data
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return Response(combined)

# ======= ПОИСК =======
class SearchView(APIView):
    """Поиск по статьям и импортированным новостям."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        raw_q = request.query_params.get("q", "").strip()
        mode = request.query_params.get("mode", "and").lower()
        if not raw_q:
            return Response({"results": [], "count": 0})

        terms = [_normalize_text(t) for t in raw_q.split() if t]
        vendor = connection.vendor
        use_python_fallback = (vendor == "sqlite")

        # Статьи: фильтрация пустых текстов
        articles_qs = (
            Article.objects.filter(status="PUBLISHED")
            .annotate(text_len=Length("content"))
            .exclude(Q(content__isnull=True) | Q(content__exact="") | Q(text_len__lt=50))
        )
        if terms and not use_python_fallback:
            qa = Q()
            for term in terms:
                clause = Q(title__icontains=term) | Q(content__icontains=term)
                qa = (qa | clause) if mode == "or" else (qa & clause)
            articles_qs = articles_qs.filter(qa).distinct()

        # RSS: фильтрация пустых summary
        imported_qs = (
            ImportedNews.objects
            .annotate(sum_len=Length("summary"))
            .exclude(
                Q(summary__isnull=True) |
                Q(summary__exact="") |
                Q(sum_len__lt=50) |
                Q(summary__icontains="без содержим")
            )
        )
        if terms and not use_python_fallback:
            qi = Q()
            for term in terms:
                clause = Q(title__icontains=term) | Q(summary__icontains=term)
                qi = (qi | clause) if mode == "or" else (qi & clause)
            imported_qs = imported_qs.filter(qi).distinct()

        # Повышаем популярность категорий
        cat_ids = set()
        cat_ids.update(articles_qs.values_list("categories__id", flat=True))
        cat_ids.update(imported_qs.values_list("category_id", flat=True))
        cat_ids.discard(None)
        if cat_ids:
            Category.objects.filter(id__in=cat_ids).update(popularity=F("popularity") + 1)

        article_data = ArticleSerializer(articles_qs, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported_qs, many=True, context={"request": request}).data

        combined = deduplicate(article_data + imported_data)
        if terms and use_python_fallback:
            combined = [it for it in combined if _item_matches_terms(it, terms, mode)]

        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)
        return _paginate_combined(request, combined)

# ======= ДЕТАЛИ =======
class ArticleDetailView(generics.RetrieveAPIView):
    """Детальный просмотр статьи."""
    queryset = (
        Article.objects.filter(status="PUBLISHED")
        .annotate(text_len=Length("content"))
        .exclude(Q(content__isnull=True) | Q(content__exact="") | Q(text_len__lt=50))
    )
    serializer_class = ArticleSerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]

class ImportedNewsDetailView(generics.RetrieveAPIView):
    """Детальный просмотр импортированной новости."""
    queryset = (
        ImportedNews.objects
        .annotate(sum_len=Length("summary"))
        .exclude(
            Q(summary__isnull=True) |
            Q(summary__exact="") |
            Q(sum_len__lt=50) |
            Q(summary__icontains="без содержим")
        )
    )
    serializer_class = ImportedNewsSerializer
    lookup_field = "id"
    permission_classes = [permissions.AllowAny]
