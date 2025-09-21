# backend/pages/views.py
# Назначение: API для получения страниц по slug.

from rest_framework.generics import RetrieveAPIView, ListAPIView
from .models import StaticPage
from .serializers import StaticPageSerializer


class PageDetailView(RetrieveAPIView):
    queryset = StaticPage.objects.filter(is_published=True)
    serializer_class = StaticPageSerializer
    lookup_field = "slug"


class PageListView(ListAPIView):
    queryset = StaticPage.objects.filter(is_published=True)
    serializer_class = StaticPageSerializer

