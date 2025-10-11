# Путь: backend/news/views_universal_detail.py
# Назначение: Универсальная детальная страница новости (Article или ImportedNews).
# Исправлено:
#   ✅ Поиск новости по slug в обеих моделях.
#   ✅ Поддержка общих SEO-URL /api/news/<slug>/.
#   ✅ Возврат JSON-ответа для фронтенда React.
#   ✅ Если не найдено — корректный 404.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Article, ImportedNews
from .serializers import ArticleSerializer, ImportedNewsSerializer


class UniversalNewsDetailView(APIView):
    """
    Универсальный контроллер для детальной новости.
    Работает для:
      • Article (авторские / вручную добавленные)
      • ImportedNews (из RSS)
    """

    def get(self, request, slug):
        # Сначала пробуем найти в Article
        article = Article.objects.filter(slug=slug).first()
        if article:
            data = ArticleSerializer(article, context={"request": request}).data
            return Response(data, status=status.HTTP_200_OK)

        # Потом пробуем в ImportedNews
        imported = ImportedNews.objects.filter(slug=slug).first()
        if imported:
            data = ImportedNewsSerializer(imported, context={"request": request}).data
            return Response(data, status=status.HTTP_200_OK)

        # Если нигде не найдено — возвращаем 404
        return Response({"detail": "Новость не найдена."}, status=status.HTTP_404_NOT_FOUND)
