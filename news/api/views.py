# backend/news/api/views.py
# Назначение: Пример DRF ViewSet с автоматической фильтрацией «пустых» новостей.
# Если у вас уже есть свой файл — просто добавьте NonEmptyNewsMixin к вашим ViewSet.
# Путь: backend/news/api/views.py

from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .mixins import NonEmptyNewsMixin
from .. import models
from ..serializers import ArticleSerializer, ImportedNewsSerializer

class DefaultPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

class ArticleViewSet(NonEmptyNewsMixin, ReadOnlyModelViewSet):
    """
    /api/news/article/<slug>/
    /api/news/article/?page=1
    """
    queryset = models.Article.objects.all().order_by("-published_at", "-id")
    serializer_class = ArticleSerializer
    pagination_class = DefaultPagination
    lookup_field = "slug"

class ImportedNewsViewSet(NonEmptyNewsMixin, ReadOnlyModelViewSet):
    """
    /api/news/imported/<id>/
    /api/news/imported/?page=1
    """
    queryset = models.ImportedNews.objects.all().order_by("-published_at", "-id")
    serializer_class = ImportedNewsSerializer
    pagination_class = DefaultPagination
    lookup_field = "pk"

class CategoryViewSet(ReadOnlyModelViewSet):
    """
    /api/news/category/<slug>/?page=1
    Внутри — только непустые новости, благодаря ручке related.
    """
    queryset = models.Category.objects.all()
    pagination_class = DefaultPagination
    serializer_class = None  # не обязателен, покажем related через action

    @action(detail=True, methods=["get"], url_path="")
    def list_news(self, request, pk=None):
        category = get_object_or_404(models.Category, slug=pk)
        # Берём и статьи, и импортированные — объединяем, убираем пустые.
        from ..utils.content_filters import filter_nonempty
        articles = filter_nonempty(category.article_set.all())
        imported = filter_nonempty(category.importednews_set.all())
        # Склеиваем вручную (упрощённо) — на реальном проекте лучше отдельный сериализатор.
        data = []
        for a in articles[:100]:
            data.append(ArticleSerializer(a).data)
        for i in imported[:100]:
            data.append(ImportedNewsSerializer(i).data)
        # Сортировка по дате:
        data.sort(key=lambda x: (x.get("published_at") or ""), reverse=True)
        return Response({"results": data})
