# Путь: backend/news/views_compat.py
# Назначение: Совместимость для старых/ошибочных фронтовых запросов, чтобы убрать 404.
#   • /api/news/related/?slug=<slug>                 → вызывает related_news(...)
#   • /api/news/<slug>/?limit=.. или ?page=..        → отдаёт ленту КАТЕГОРИИ <slug>
#   • /api/news/hit/                                 → алиас для HitMetricsView (если фронт ждёт старый путь)
#   • /api/news/upload/                              → алиас для upload_image

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpRequest

from .views import (
    CategoryNewsView,
    related_news,
    HitMetricsView,
)
from .views_universal_detail import UniversalNewsDetailView
from .views_upload import upload_image


@api_view(["GET"])
def related_news_compat(request: HttpRequest):
    """
    Совместимость: /api/news/related/?slug=<slug>
    """
    slug = request.GET.get("slug")
    if not slug:
        return Response({"detail": "Missing slug query param"}, status=status.HTTP_400_BAD_REQUEST)
    return related_news(request, slug=slug)


def category_or_article_compat(request: HttpRequest, slug: str, *args, **kwargs):
    """
    Совместимость: /api/news/<slug>/
      - если присутствует limit/page → это запрос списка новостей КАТЕГОРИИ <slug>
      - иначе → универсальная детальная страница новости
    """
    if any(k in request.GET for k in ("limit", "page")):
        return CategoryNewsView.as_view()(request, slug=slug, *args, **kwargs)
    return UniversalNewsDetailView.as_view()(request, slug=slug, *args, **kwargs)


# Алиас-обёртка для метрики, чтобы принимался старый путь /news/hit/
class HitMetricsCompatView(HitMetricsView):
    """
    POST /api/news/hit/ → поведение как у /api/news/metrics/hit/
    """
    pass


# Алиас-обёртка загрузки, чтобы принимался старый путь /news/upload/
def upload_image_compat(request: HttpRequest, *args, **kwargs):
    """
    POST /api/news/upload/ → поведение как у /api/upload-image/
    """
    return upload_image(request, *args, **kwargs)
