# ===== ФАЙЛ: backend/news/views.py =====
# ПУТЬ: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\backend\news\views.py
# НАЗНАЧЕНИЕ: Представления DRF для работы с новостями и категориями.
# ОПИСАНИЕ: Содержит публичные ленты, создание новостей авторами и модерацию редакторами.

from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

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


class AuthorNewsCreateView(generics.CreateAPIView):
    """Создание новости автором"""
    serializer_class = NewsCreateSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserNewsListView(generics.ListAPIView):
    """Новости текущего пользователя"""
    serializer_class = NewsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return News.objects.filter(author=self.request.user).order_by("-created_at")


class PendingNewsListView(generics.ListAPIView):
    """Список новостей, ожидающих модерации"""
    serializer_class = NewsSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return News.objects.filter(is_moderated=False).order_by("created_at")


class ApproveNewsView(APIView):
    """Подтверждение новости редактором"""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        news = get_object_or_404(News, pk=pk, is_moderated=False)
        news.is_moderated = True
        news.save()
        return Response({"status": "approved"})
