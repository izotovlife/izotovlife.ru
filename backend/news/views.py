# backend/news/views.py
# Путь: backend/news/views.py
# Назначение: API-представления для работы с новостями и категориями.

from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import News, Category
from .serializers import NewsSerializer, CategorySerializer, NewsCreateSerializer

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

