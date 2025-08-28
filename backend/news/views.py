# backend/news/views.py
# Путь: backend/news/views.py
# Назначение: API-представления для работы с новостями и категориями.

from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import News, Category, Favorite
from .serializers import (
    NewsSerializer,
    CategorySerializer,
    NewsCreateSerializer,
    FavoriteSerializer,
)

class NewsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

class NewsListView(generics.ListAPIView):
    queryset = News.objects.filter(is_moderated=True).order_by("-created_at")
    serializer_class = NewsSerializer
    pagination_class = NewsPagination
    permission_classes = [permissions.AllowAny]

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class PopularNewsView(generics.ListAPIView):
    queryset = News.objects.filter(is_moderated=True).order_by("-id")[:10]
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]


class NewsCreateView(generics.CreateAPIView):
    """Создание новости автором (уходит на модерацию)."""

    serializer_class = NewsCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(
            author=self.request.user,
            source_type="author",
            is_moderated=False,
        )


class NewsModerationListView(generics.ListAPIView):
    """Список новостей, ожидающих модерации (доступно редакторам)."""

    queryset = News.objects.filter(is_moderated=False)
    serializer_class = NewsSerializer
    permission_classes = [permissions.IsAdminUser]


class NewsApproveView(generics.GenericAPIView):
    """Одобрение новости редактором."""

    queryset = News.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = NewsSerializer

    def post(self, request, pk, *args, **kwargs):
        news = self.get_object()
        news.is_moderated = True
        news.save()
        return Response(self.get_serializer(news).data, status=status.HTTP_200_OK)


class FavoriteListView(generics.ListAPIView):
    """Список избранных новостей текущего пользователя."""

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)


class FavoriteView(generics.GenericAPIView):
    """Добавление и удаление новости из избранного."""

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, news_id):
        news = get_object_or_404(News, id=news_id)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, news=news
        )
        serializer = self.get_serializer(favorite)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    def delete(self, request, news_id):
        Favorite.objects.filter(user=request.user, news_id=news_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

