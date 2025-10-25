# Путь: backend/news/views.py
# Назначение: API для новостей — лента, категории, поиск, детальные страницы и «Похожие новости».
# Что нового/исправлено:
#   ✅ «Мягкая» пагинация: при page > pages возвращаем 200 и пустой список (не 404)
#   ✅ HitMetricsView принимает payload с ключом slug ИЛИ type (совместимость с фронтом)
#   ✅ only_with_meaningful_text — безопасный inline-фильтр для ImportedNews
#   ✅ Images/Text фиды обратно на request.query_params
#   ✅ Related работает универсально как по /news/<slug>/related/, так и по /news/related/<slug>/
#   ✅ UniversalNewsDetailView — отдаёт Article или ImportedNews по slug
#   ♻️ Удалено (для корректности): вложенная функция suggest_news внутри класса RelatedNewsViewUniversal,
#      а также дублирующие импорты DRF (они мешали статическому анализу). Функционала не лишились.

from django.db import connection
from django.db.models import Q, Count, F, Value, CharField
from django.db.models.functions import Length, Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET

from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

import json

from .models import Article, Category, ImportedNews
from .serializers import ArticleSerializer, ImportedNewsSerializer, CategorySerializer


# ===========================================================
# «МЯГКАЯ» ПОМОЩЬНЫЕ
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


# ✅ ФИЛЬТР СОДЕРЖАТЕЛЬНОСТИ ДЛЯ RSS (inline и безопасный к отсутствию полей)
def only_with_meaningful_text(
    qs,
    min_chars: int = 120,
    summary_field: str = "summary",
    content_field: str = "content",
):
    """
    Оставляет ImportedNews с достаточно длинным текстом.
    Берём summary, если пуст — content (если поле существует). Порог — min_chars.
    """
    model = qs.model

    def has_field(name: str) -> bool:
        try:
            model._meta.get_field(name)
            return True
        except Exception:
            return False

    has_summary = has_field(summary_field)
    has_content = has_field(content_field)

    if has_summary and has_content:
        effective_text = Coalesce(
            F(summary_field),
            F(content_field),
            Value("", output_field=CharField()),
            output_field=CharField(),
        )
    elif has_summary:
        effective_text = Coalesce(
            F(summary_field),
            Value("", output_field=CharField()),
            output_field=CharField(),
        )
    elif has_content:
        effective_text = Coalesce(
            F(content_field),
            Value("", output_field=CharField()),
            output_field=CharField(),
        )
    else:
        effective_text = Value("", output_field=CharField())

    return qs.annotate(_text_len=Length(effective_text)).filter(_text_len__gte=min_chars)


# ===========================================================
# ПАГИНАЦИЯ (мягкая)
# ===========================================================

class NewsFeedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50

    # Делать «мягко»: вместо NotFound -> пустая страница и 200
    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view=view)
        except NotFound:
            # Синтезируем мета, чтобы get_paginated_response мог отработать
            # Но так как PageNumberPagination жёстко завязан на self.page,
            # проще в местах вызова перехватывать NotFound и отдавать ручной ответ.
            raise


def _soft_paginated_response_for_list(request, items, page_size_default=20):
    """
    Используется когда перехватываем NotFound и хотим отдать «мягкий» 200.
    """
    try:
        page = int(request.query_params.get("page", "1") or "1")
    except ValueError:
        page = 1
    try:
        page_size = int(request.query_params.get("page_size", str(page_size_default)) or page_size_default)
    except ValueError:
        page_size = page_size_default

    total = len(items)
    pages = (total + page_size - 1) // max(1, page_size)
    return Response({
        "count": total,
        "next": None,
        "previous": None,
        "results": [],
        "page": page,
        "pages": pages,
    }, status=200)


def _paginate_combined(request, combined):
    """
    Универсальная пагинация для готовых списков (images/text/search).
    Поддерживает limit/offset, иначе — PageNumberPagination.
    """
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
    try:
        page = paginator.paginate_queryset(combined, request)
    except NotFound:
        return _soft_paginated_response_for_list(request, combined, page_size_default=paginator.page_size)

    resp = paginator.get_paginated_response(page)
    data = resp.data
    if "results" in data and "items" not in data:
        data["items"] = data["results"]
    return resp


# ===========================================================
# ФОРМА «ПРЕДЛОЖИТЬ НОВОСТЬ»
# (у тебя в urls подключён отдельный views_suggest; этот CBV оставляю на случай использования тут)
# ===========================================================

class SuggestNewsView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        # Honeypot
        if data.get("website"):
            return Response({"ok": False, "error": "spam"}, status=400)

        required = ["first_name", "last_name", "email", "message"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return Response({"ok": False, "error": f"Отсутствуют поля: {', '.join(missing)}"}, status=400)

        # TODO: запись в БД/отправка e-mail
        return Response({"ok": True}, status=200)


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

        imported = ImportedNews.objects.annotate(sum_len=Length("summary")).exclude(
            Q(summary__isnull=True) | Q(summary__exact="") | Q(sum_len__lt=50)
        )
        if category_slug:
            imported = imported.filter(category__slug=category_slug)

        # ✅ скрываем «только фото + заголовок»
        imported = only_with_meaningful_text(imported, min_chars=120)

        combined = list(articles) + list(imported)
        combined.sort(
            key=lambda x: getattr(x, "published_at", None) or getattr(x, "created_at", None) or "",
            reverse=True,
        )
        return combined

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        try:
            page = self.paginate_queryset(queryset)
        except NotFound:
            return _soft_paginated_response_for_list(request, list(queryset), page_size_default=self.pagination_class.page_size)

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

        articles = Article.objects.filter(status="PUBLISHED").exclude(
            Q(cover_image__isnull=True) | Q(cover_image="")
        )
        imported = ImportedNews.objects.exclude(Q(image__isnull=True) | Q(image=""))

        if category_slug:
            articles = articles.filter(categories__slug=category_slug)
            imported = imported.filter(category__slug=category_slug)

        imported = only_with_meaningful_text(imported, min_chars=120)

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data

        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)

        return _paginate_combined(request, combined)


class NewsFeedTextView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category_slug = request.query_params.get("category")

        articles = Article.objects.filter(status="PUBLISHED").filter(
            Q(cover_image__isnull=True) | Q(cover_image="")
        )
        imported = ImportedNews.objects.filter(Q(image__isnull=True) | Q(image=""))

        if category_slug:
            articles = articles.filter(categories__slug=category_slug)
            imported = imported.filter(category__slug=category_slug)

        imported = only_with_meaningful_text(imported, min_chars=120)

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
    GET /api/news/category/<slug>/?page=&page_size=
    Объединённая лента Article + ImportedNews для выбранной категории.
    «Мягкая» пагинация: при выходе за пределы — 200 и пустой results.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)

        # Немного телеметрии
        Category.objects.filter(id=category.id).update(popularity=F("popularity") + 1)

        articles = Article.objects.filter(status="PUBLISHED", categories=category)
        imported = ImportedNews.objects.filter(category=category)
        imported = only_with_meaningful_text(imported, min_chars=120)

        article_data = ArticleSerializer(articles, many=True, context={"request": request}).data
        imported_data = ImportedNewsSerializer(imported, many=True, context={"request": request}).data

        combined = deduplicate(article_data + imported_data)
        combined.sort(key=lambda x: x.get("published_at") or x.get("created_at") or "", reverse=True)

        paginator = NewsFeedPagination()
        try:
            page = paginator.paginate_queryset(combined, request)
        except NotFound:
            return _soft_paginated_response_for_list(request, combined, page_size_default=paginator.page_size)

        if page is not None:
            return paginator.get_paginated_response(page)
        return Response({"results": combined, "count": len(combined)})


# ===========================================================
# ПОИСК (обычный)
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
            # Упрощённый websearch (GIN)
            article_qs = article_qs.extra(
                where=["to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(content,'')) @@ plainto_tsquery('russian', %s)"],
                params=[raw_q]
            )
            imported_qs = imported_qs.extra(
                where=["to_tsvector('russian', coalesce(title,'') || ' ' || coalesce(summary,'')) @@ plainto_tsquery('russian', %s)"],
                params=[raw_q]
            )
        else:
            article_qs = article_qs.filter(Q(title__icontains=raw_q) | Q(content__icontains=raw_q))
            imported_qs = imported_qs.filter(Q(title__icontains=raw_q) | Q(summary__icontains=raw_q))

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

        is_pg = connection.vendor == "postgresql"

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


# ===========================================================
# ПОХОЖИЕ
# ===========================================================

@require_GET
def related_news(request, *args, **kwargs):
    """
    Возвращает похожие статьи или импортированные новости.
    Работает с:
      • /api/news/<slug>/related/
      • /api/news/related/<slug>/
      • (совместимость) /api/news/<category>/<slug>/related/, /api/news/source/<source>/<slug>/related/
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
        current = Article.objects.filter(slug=slug, status="PUBLISHED").first() or ImportedNews.objects.filter(slug=slug).first()
        type_ = "rss" if isinstance(current, ImportedNews) else "article"

    if not current:
        # Пусть это будет «мягкий» 404: фронту проще проверить results=[]
        return JsonResponse({"results": [], "error": "not found"}, status=404)

    title = getattr(current, "title", "") or ""
    terms = [t for t in title.split() if len(t) > 3]
    query = Q()
    for t in terms:
        query |= Q(title__icontains=t)

    if type_ == "article":
        qs = (
            Article.objects.filter(status="PUBLISHED")
            .exclude(pk=current.pk)
            .filter(query)
            .order_by("-published_at")[:max_results]
        )
        data = ArticleSerializer(qs, many=True, context={"request": request}).data
    else:
        qs = (
            ImportedNews.objects.filter(source_fk=getattr(current, "source_fk", None))
            .exclude(pk=current.pk)
            .filter(query)
            .order_by("-published_at")[:max_results]
        )
        data = ImportedNewsSerializer(qs, many=True, context={"request": request}).data

    return JsonResponse({"results": data[:max_results]})


# ===========================================================
# МЕТРИКИ (фикс 405 и совместимость с фронтом: slug ИЛИ type)
# ===========================================================

class HitMetricsView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data or {}
            # Совместимость: принимаем и slug, и type (как в твоих логах)
            slug = (data.get("slug") or data.get("type") or "").strip()
            if not slug:
                return Response({"error": "slug required"}, status=status.HTTP_400_BAD_REQUEST)

            news_obj = (
                Article.objects.filter(slug=slug).first()
                or ImportedNews.objects.filter(slug=slug).first()
            )

            if not news_obj:
                return Response(
                    {"error": f"Новость '{slug}' не найдена"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            news_obj.views_count = (getattr(news_obj, "views_count", 0) or 0) + 1
            news_obj.save(update_fields=["views_count"])

            return Response(
                {"message": "ok", "views_count": news_obj.views_count},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
