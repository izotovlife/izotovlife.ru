# Путь: backend/news/views_favorites.py
# Назначение: Эндпоинты избранного: список, проверить статус по слагу, переключить.

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models_favorites import Favorite
from .serializers_favorites import FavoriteItemSerializer

# Импортируем ваши модели новостей. Если имена у вас отличаются — поправьте импорты ниже.
from .models import Article  # модель «ручных» статей
try:
    from .models import ImportedNews  # импортированные из RSS
    HAS_IMPORTED = True
except Exception:
    HAS_IMPORTED = False


def _resolve_by_slug(slug):
    """
    Пытаемся найти новость по слагу сначала среди Article, затем среди ImportedNews.
    Вернём (obj, content_type).
    """
    obj = Article.objects.filter(slug=slug).first()
    if obj:
        return obj, ContentType.objects.get_for_model(Article)

    if HAS_IMPORTED:
        obj = ImportedNews.objects.filter(slug=slug).first()
        if obj:
            return obj, ContentType.objects.get_for_model(ImportedNews)

    return None, None


def _extract_meta(obj):
    """
    Собираем удобные мета-данные, чтобы быстро рисовать избранное в кабинете:
    title, slug, preview_image, source_name, published_at.
    Пытаемся учесть разные имена полей.
    """
    title = getattr(obj, "title", "") or getattr(obj, "name", "") or ""
    slug = getattr(obj, "slug", "") or ""
    # Картинка: image / cover / thumbnail / preview_image
    preview = (
        getattr(obj, "image", None)
        or getattr(obj, "cover", None)
        or getattr(obj, "thumbnail", None)
        or getattr(obj, "preview_image", None)
    )
    if preview:
        preview = str(preview)
    else:
        preview = ""

    # Источник: если есть source_fk или source/name
    source_name = ""
    src = getattr(obj, "source_fk", None) or getattr(obj, "source", None)
    if src:
        source_name = getattr(src, "name", "") or str(src)

    published_at = (
        getattr(obj, "published_at", None)
        or getattr(obj, "created_at", None)
        or getattr(obj, "date", None)
    )

    return {
        "title": title,
        "slug": slug,
        "preview_image": preview,
        "source_name": source_name or "",
        "published_at": published_at,
    }


class FavoriteListView(generics.ListAPIView):
    """
    GET /api/news/favorites/
    Вернёт список избранного ТЕКУЩЕГО пользователя.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FavoriteItemSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).order_by("-created_at")


@api_view(["GET"])
def favorite_check(request):
    """
    GET /api/news/favorites/check/?slug=...
    Анонимам возвращаем favorited=false (чтобы фронт корректно рисовал пустое сердечко).
    """
    slug = request.query_params.get("slug")
    if not slug:
        return Response({"detail": "slug is required"}, status=status.HTTP_400_BAD_REQUEST)

    if not request.user.is_authenticated:
        return Response({"favorited": False})

    obj, ct = _resolve_by_slug(slug)
    if not obj:
        return Response({"favorited": False})

    exists = Favorite.objects.filter(
        user=request.user,
        content_type=ct,
        object_id=obj.pk
    ).exists()
    return Response({"favorited": exists})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def favorite_toggle(request):
    """
    POST /api/news/favorites/toggle/
    { "slug": "<slug>" }
    Переключает состояние избранного для текущего пользователя.
    """
    slug = request.data.get("slug")
    if not slug:
        return Response({"detail": "slug is required"}, status=status.HTTP_400_BAD_REQUEST)

    obj, ct = _resolve_by_slug(slug)
    if not obj:
        return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)

    fav, created = Favorite.objects.get_or_create(
        user=request.user,
        content_type=ct,
        object_id=obj.pk,
        defaults=_extract_meta(obj),
    )

    if not created:
        # уже было — удаляем (toggle off)
        fav.delete()
        return Response({"favorited": False})

    # только что добавили
    return Response({"favorited": True})
