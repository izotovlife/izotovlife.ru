# backend/news/author_views.py
# Назначение: CRUD для авторских статей + действия автора (submit, resubmit, withdraw).
# Путь: backend/news/author_views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Article
from .serializers import ArticleSerializer


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Автор может редактировать свои статьи, если они не ушли в модерацию или не опубликованы."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Только автор может менять статью
        if obj.author != request.user and not request.user.is_staff:
            return False

        # Разрешаем редактировать только черновики и статьи на доработке
        return obj.status in [Article.Status.DRAFT, Article.Status.NEEDS_REVISION]


class AuthorArticleViewSet(viewsets.ModelViewSet):
    """
    /api/news/author/articles/
    CRUD для авторов + отправка/отзыв на модерацию.
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

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Первичная отправка статьи на модерацию (только черновики)."""
        article = self.get_object()
        if article.status != Article.Status.DRAFT:
            return Response({"detail": "Отправлять можно только черновики"},
                            status=status.HTTP_400_BAD_REQUEST)

        article.status = Article.Status.PENDING
        article.save()
        return Response(ArticleSerializer(article).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def resubmit(self, request, pk=None):
        """Повторная отправка после доработки (только для NEEDS_REVISION)."""
        article = self.get_object()
        if article.status != Article.Status.NEEDS_REVISION:
            return Response({"detail": "Повторно отправить можно только статьи на доработке"},
                            status=status.HTTP_400_BAD_REQUEST)

        article.status = Article.Status.PENDING
        article.save()
        return Response(ArticleSerializer(article).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        """Автор может отозвать статью, пока она на модерации."""
        article = self.get_object()
        if article.status != Article.Status.PENDING:
            return Response({"detail": "Отозвать можно только статьи на модерации"},
                            status=status.HTTP_400_BAD_REQUEST)

        article.status = Article.Status.DRAFT
        article.save()
        return Response(ArticleSerializer(article).data, status=status.HTTP_200_OK)
