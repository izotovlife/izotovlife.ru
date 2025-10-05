# backend/pages/views.py
# Назначение: Публичное API для статических страниц (по slug и списком).

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import StaticPage
from .serializers import StaticPagePublicSerializer


CACHE_TTL = 60 * 5  # 5 минут. Убери/измени при желании.


class PageDetailView(RetrieveAPIView):
    """
    Детальная страница по slug.
    Доступна всем, но только опубликованные записи.
    """
    permission_classes = [AllowAny]
    serializer_class = StaticPagePublicSerializer
    lookup_field = "slug"

    def get_queryset(self):
        # Только опубликованные, и выбираем только нужные поля
        return (
            StaticPage.objects.filter(is_published=True)
            .only("id", "title", "slug", "content", "created_at", "updated_at")
        )

    @method_decorator(cache_page(CACHE_TTL))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PageListView(ListAPIView):
    """
    Список опубликованных страниц.
    Параметры:
      - ?q=строка — простой поиск по title/content
      - ?limit=число — размер страницы (по умолчанию 100)
      - ?offset=число — смещение
    """
    permission_classes = [AllowAny]
    serializer_class = StaticPagePublicSerializer

    def get_queryset(self):
        qs = (
            StaticPage.objects.filter(is_published=True)
            .only("id", "title", "slug", "content", "created_at", "updated_at")
            .order_by("-updated_at")
        )
        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(content__icontains=q)
        return qs

    def list(self, request, *args, **kwargs):
        """
        Простейшая keyset-пагинация через limit/offset без DRF-пагинатора,
        чтобы не ломать фронт, который ждёт массив или {results, count}.
        """
        qs = self.get_queryset()
        try:
            limit = int(request.query_params.get("limit", 100))
        except Exception:
            limit = 100
        try:
            offset = int(request.query_params.get("offset", 0))
        except Exception:
            offset = 0

        total = qs.count()
        items = qs[offset : offset + limit]
        data = self.get_serializer(items, many=True).data

        # Совместимость: возвращаем плоский массив,
        # но и фронту удобно иметь count.
        # Если хочешь строго {results, count}, раскомментируй блок ниже.
        # return Response({"results": data, "count": total})

        resp = Response(data)
        resp["X-Total-Count"] = str(total)  # полезный хедер на будущее
        return resp

    @method_decorator(cache_page(CACHE_TTL))
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

