# Путь: backend/news/views_universal_detail.py
# Назначение: Универсальные детальные эндпоинты для Article и ImportedNews,
# с корректной выдачей изображений и SEO-friendly URL.

from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Article, ImportedNews
from .serializers import ArticleSerializer, ImportedNewsSerializer

class UniversalNewsDetailView(RetrieveAPIView):
    """
    Универсальный SEO-friendly endpoint для /api/news/<slug>/
    Возвращает Article или ImportedNews по slug с корректными URL изображений.
    """
    permission_classes = []

    def retrieve(self, request, *args, **kwargs):
        slug = kwargs.get("slug")

        article = Article.objects.filter(slug=slug, status="PUBLISHED").first()
        if article:
            serializer = ArticleSerializer(article, context={"request": request})
            data = serializer.data
            data["type"] = "article"
            return Response(data)

        imported = ImportedNews.objects.filter(slug=slug).first()
        if imported:
            serializer = ImportedNewsSerializer(imported, context={"request": request})
            data = serializer.data
            data["type"] = "rss"
            return Response(data)

        return Response({"detail": "Not found"}, status=404)


class RelatedNewsViewUniversal(APIView):
    """
    Эндпоинт: GET /api/news/<slug>/related/
    Возвращает похожие новости с правильными URL изображений.
    """
    permission_classes = []

    def get(self, request, slug):
        current = (
            Article.objects.filter(slug=slug, status="PUBLISHED").first()
            or ImportedNews.objects.filter(slug=slug).first()
        )
        if not current:
            return Response({"results": [], "error": "not found"}, status=404)

        title = getattr(current, "title", "") or ""
        terms = [t for t in title.split() if len(t) > 3]
        query = Q()
        for t in terms:
            query |= Q(title__icontains=t)

        if isinstance(current, Article):
            qs = (
                Article.objects.filter(status="PUBLISHED")
                .exclude(pk=current.pk)
                .filter(query)
                .order_by("-published_at")[:20]
            )
            serializer = ArticleSerializer(qs, many=True, context={"request": request})
        else:
            qs = (
                ImportedNews.objects.exclude(pk=current.pk)
                .filter(query)
                .order_by("-published_at")[:20]
            )
            serializer = ImportedNewsSerializer(qs, many=True, context={"request": request})

        return Response({"results": serializer.data})
