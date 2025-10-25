# Путь: backend/news/views_category_proxy.py
# Назначение: Совместимый эндпоинт GET /api/news/<category_slug>/
#   Возвращает последние публикации этой категории (из Article и ImportedNews).
#   Нужен для гашения 404 от старого фронта и мягкой миграции.
# Параметры: ?limit=8 (по умолчанию), ?offset=0

from django.http import JsonResponse, HttpResponseBadRequest
from django.apps import apps
from django.db.models import Q
from django.utils import timezone

def _get_model(app, name):
    try:
        return apps.get_model(app, name)
    except Exception:
        return None

def _first_image(obj):
    # пробуем популярные поля
    for name in ("image", "cover_image", "cover", "preview_image", "image_url", "thumbnail", "poster"):
        v = getattr(obj, name, None)
        if not v:
            continue
        # FileField / ImageField
        url = getattr(v, "url", None)
        if isinstance(url, str) and url:
            return url
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None

def _obj_to_dict(obj, category_slug):
    return {
        "id": getattr(obj, "pk", None),
        "slug": getattr(obj, "slug", None) or "",
        "title": getattr(obj, "title", None) or getattr(obj, "name", None) or "",
        "image": _first_image(obj),
        "category": {
            "slug": category_slug,
        },
        "published_at": getattr(obj, "published_at", None) or getattr(obj, "created_at", None) or getattr(obj, "date", None),
        "source": getattr(obj, "source_title", None) or getattr(obj, "source", None) or "",
    }

def category_latest_proxy(request, category_slug: str):
    Category = _get_model("news", "Category")
    if not Category:
        return HttpResponseBadRequest("Category model not found")

    limit = 8
    offset = 0
    try:
        limit = max(1, min(int(request.GET.get("limit", "8")), 50))
    except Exception:
        pass
    try:
        offset = max(0, int(request.GET.get("offset", "0")))
    except Exception:
        pass

    # сверим, что категория существует (если нет — вернём пусто, но 200)
    cat = Category.objects.filter(slug=category_slug).first()

    Article = _get_model("news", "Article")
    ImportedNews = _get_model("news", "ImportedNews")

    items = []

    # Article: чаще всего M2M categories
    if Article:
        qs = Article.objects.all()
        # пытаемся отфильтровать по категории
        if hasattr(Article, "categories"):
            try:
                qs = qs.filter(categories__slug=category_slug)
            except Exception:
                pass
        elif hasattr(Article, "category"):
            try:
                qs = qs.filter(category__slug=category_slug)
            except Exception:
                pass
        elif hasattr(Article, "category_slug"):
            try:
                qs = qs.filter(category_slug=category_slug)
            except Exception:
                pass
        # сортировка по датам, какие найдём
        order_fields = [f for f in ("-published_at", "-created_at", "-date", "-id") if hasattr(Article, f.replace("-", ""))]
        if order_fields:
            try:
                qs = qs.order_by(*order_fields)
            except Exception:
                pass
        for obj in qs[offset:offset+limit]:
            items.append(_obj_to_dict(obj, category_slug))

    # ImportedNews: обычно FK category
    if ImportedNews and len(items) < limit:
        qs = ImportedNews.objects.all()
        if hasattr(ImportedNews, "category"):
            try:
                qs = qs.filter(category__slug=category_slug)
            except Exception:
                pass
        elif hasattr(ImportedNews, "category_slug"):
            try:
                qs = qs.filter(category_slug=category_slug)
            except Exception:
                pass
        order_fields = [f for f in ("-published_at", "-created_at", "-date", "-id") if hasattr(ImportedNews, f.replace("-", ""))]
        if order_fields:
            try:
                qs = qs.order_by(*order_fields)
            except Exception:
                pass
        for obj in qs[offset:offset+limit-len(items)]:
            items.append(_obj_to_dict(obj, category_slug))

    # даже если категории нет — вернём пустой список, чтобы фронт не шумел 404
    return JsonResponse({
        "category": category_slug,
        "count": len(items),
        "results": items,
        "offset": offset,
        "limit": limit,
        "timestamp": timezone.now().isoformat(),
    })
