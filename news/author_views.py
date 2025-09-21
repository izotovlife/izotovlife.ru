# backend/news/author_views.py
# Назначение: CRUD для авторских статей + ручки модерации для редактора.
# Путь: backend/news/author_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Article
from .serializers import ArticleSerializer


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Автор может редактировать свои статьи, редактор/админ — читать всё."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff


class AuthorArticleViewSet(viewsets.ModelViewSet):
    """
    /api/news/author/articles/
    CRUD для авторов.
    """
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, "is_editor", lambda: False)():
            return Article.objects.all()
        return Article.objects.filter(author=user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# ====== Редакторские ручки ======

@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def moderation_queue(request):
    """
    /api/news/author/moderation-queue/
    Возвращает статьи со статусом PENDING (на модерации).
    """
    if not (request.user.is_superuser or getattr(request.user, "is_editor", lambda: False)()):
        return Response({"detail": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

    items = Article.objects.filter(status=Article.Status.PENDING).order_by("created_at")
    return Response(ArticleSerializer(items, many=True).data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def review_article(request, pk, action):
    """
    /api/news/author/review/<id>/<action>/
    Редактор публикует статью или отправляет на доработку.
    """
    if not (request.user.is_superuser or getattr(request.user, "is_editor", lambda: False)()):
        return Response({"detail": "Нет доступа"}, status=status.HTTP_403_FORBIDDEN)

    article = get_object_or_404(Article, pk=pk)

    notes = request.data.get("notes", "")
    article.editor_notes = notes

    if action == "publish":
        article.status = Article.Status.PUBLISHED
        article.published_at = timezone.now()
    elif action == "revise":
        article.status = Article.Status.NEEDS_REVISION
    else:
        return Response({"detail": "Неизвестное действие"}, status=status.HTTP_400_BAD_REQUEST)

    article.save()
    return Response(ArticleSerializer(article).data)
