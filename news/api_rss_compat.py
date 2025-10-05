# Путь: backend/news/api_rss_compat.py
# Назначение: Совместимые API-вьюхи для RSS-новостей под фронтовые URL:
#   • GET /api/news/rss/source/<source>/<slug>/          → деталь импортированной новости
#   • GET /api/news/rss/source/<source>/<slug>/related/  → похожие новости того же источника
# Особенности:
#   • Нормализуем "кривые" слаги (хвостовые дефисы, двойные дефисы).
#   • Возвращаем структуру, которую ждёт фронт:
#       { title, slug, summary/content, image, published_at, link,
#         source{slug,name}, type="rss", seo_url="/news/source/<src>/<slug>/" }
#   • Ничего существующего не ломаем: это дополнительный слой совместимости.
#   • Если у модели/полей имена иные — подгоню фильтры (напишите).

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# ↙️ Замените при необходимости на вашу модель
from news.models import ImportedNews  # type: ignore


def _normalize_slug(raw: str) -> str:
    if not raw:
        return raw
    v = str(raw).strip().strip("/").strip("-")
    while "--" in v:
        v = v.replace("--", "-")
    return v


def _find_imported_news(source_slug: str, slug: str):
    """Ищем ImportedNews по источнику и разным вариантам slug."""
    if not (source_slug and slug):
        return None

    qs = ImportedNews.objects.select_related("source").filter(
        Q(source__slug=source_slug) | Q(source__code=source_slug)
    )

    candidates = []
    s1 = slug
    s2 = slug.rstrip("-")
    s3 = _normalize_slug(slug)
    for s in (s1, s2, s3):
        if s and s not in candidates:
            candidates.append(s)

    return qs.filter(slug__in=candidates).first()


def _seo_url(source_slug: str, item_slug: str) -> str:
    # ⚠️ Именно такой формат ждёт фронт (NewsDetailPage/Api.js):
    return f"/news/source/{source_slug}/{item_slug}/"


def _obj_to_dict(obj: ImportedNews) -> dict:
    src_slug = (
        getattr(obj.source, "slug", None)
        or getattr(obj.source, "code", None)
        or "source"
    )
    data = {
        # стандартные поля, которые фронт использует
        "title": getattr(obj, "title", ""),
        "slug": getattr(obj, "slug", ""),
        "summary": getattr(obj, "summary", "") or "",
        "content": getattr(obj, "content", "") or "",
        "image": getattr(obj, "image", "") or "",
        "published_at": getattr(obj, "published_at", None),
        "link": getattr(obj, "link", None),
        "source": {
            "slug": src_slug,
            "name": getattr(obj.source, "name", "") or "Источник",
        },
        # чтобы фронт и резолвер понимали тип
        "type": "rss",
        # ВАЖНО: seo_url в формате /news/source/<src>/<slug>/
        "seo_url": _seo_url(src_slug, getattr(obj, "slug", "")),
        # на случай, если фронт где-то ожидает наличие categories
        "categories": [],
    }

    # не вредно отдать доп.инфо, если есть (не ломает фронт)
    extra_keys = ("id", "created_at", "feed_url", "category", "category_display")
    for k in extra_keys:
        if hasattr(obj, k):
            data[k] = getattr(obj, k)
    return data


class ImportedNewsDetailCompat(APIView):
    """GET /api/news/rss/source/<source>/<slug>/"""
    def get(self, request, source: str, slug: str):
        obj = _find_imported_news(source, slug)
        if not obj:
            # Единообразная ошибка для фронта
            return Response({"detail": "RSS item not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(_obj_to_dict(obj), status=status.HTTP_200_OK)


class ImportedNewsRelatedCompat(APIView):
    """GET /api/news/rss/source/<source>/<slug>/related/"""
    def get(self, request, source: str, slug: str):
        current = _find_imported_news(source, slug)
        if not current:
            return Response({"results": []}, status=status.HTTP_200_OK)

        qs = (
            ImportedNews.objects.select_related("source")
            .filter(Q(source__slug=source) | Q(source__code=source))
            .exclude(pk=current.pk)
            .order_by("-published_at")[:10]
        )
        return Response({"results": [_obj_to_dict(x) for x in qs]}, status=status.HTTP_200_OK)
