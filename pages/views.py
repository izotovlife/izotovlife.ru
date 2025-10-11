# Путь: backend/pages/views.py
# Назначение: API для получения статических страниц по slug и списком.
# Исправлено:
#   ✅ Добавлена сортировка .order_by("id") для стабильной пагинации
#   ✅ Предупреждение UnorderedObjectListWarning больше не появляется

from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework import permissions
from .models import StaticPage
from .serializers import StaticPageSerializer


class PageDetailView(RetrieveAPIView):
    """Получение конкретной опубликованной страницы по slug"""
    queryset = StaticPage.objects.filter(is_published=True)
    serializer_class = StaticPageSerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]


class PageListView(ListAPIView):
    """Получение списка опубликованных статических страниц"""
    # ✅ Добавлено .order_by("id") для стабильной пагинации
    queryset = StaticPage.objects.filter(is_published=True).order_by("id")
    serializer_class = StaticPageSerializer
    permission_classes = [permissions.AllowAny]
