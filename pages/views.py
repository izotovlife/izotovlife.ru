# backend/pages/views.py
# Назначение: API для получения страниц по slug. Доступ открыт для всех.

from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework import permissions
from .models import StaticPage
from .serializers import StaticPageSerializer


class PageDetailView(RetrieveAPIView):
    queryset = StaticPage.objects.filter(is_published=True)
    serializer_class = StaticPageSerializer
    lookup_field = "slug"
    permission_classes = [permissions.AllowAny]   # ✅


class PageListView(ListAPIView):
    queryset = StaticPage.objects.filter(is_published=True)
    serializer_class = StaticPageSerializer
    permission_classes = [permissions.AllowAny]   # ✅

