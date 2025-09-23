# backend/news/editor_views.py
# Назначение: API для личного кабинета редактора — список статей на модерации, принятие/отклонение/возврат на доработку.
# Путь: backend/news/editor_views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now

from .models import Article
from .serializers import ArticleSerializer
from accounts.permissions import IsEditor


class ModerationQueueView(generics.ListAPIView):
    """Список статей на модерации (status = PENDING)."""
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsEditor]

    def get_queryset(self):
        return Article.objects.filter(status=Article.Status.PENDING).order_by("created_at")


class ReviewArticleView(APIView):
    """Действие редактора над статьей (approve / reject / needs_revision)."""
    permission_classes = [IsAuthenticated, IsEditor]

    def post(self, request, pk, action):
        try:
            article = Article.objects.get(pk=pk)
        except Article.DoesNotExist:
            return Response({"detail": "Статья не найдена"}, status=status.HTTP_404_NOT_FOUND)

        note = request.data.get("editor_notes", "")

        if action == "approve":
            article.status = Article.Status.PUBLISHED
            article.published_at = now()
            article.editor_notes = note

        elif action == "reject":
            article.status = Article.Status.DRAFT
            article.editor_notes = note or "Отклонено редактором"

        elif action == "needs_revision":
            article.status = Article.Status.NEEDS_REVISION
            article.editor_notes = note or "Нужна доработка"

        else:
            return Response({"detail": "Неверное действие"}, status=status.HTTP_400_BAD_REQUEST)

        article.save()
        return Response(ArticleSerializer(article).data, status=status.HTTP_200_OK)
