# backend/news/views.py
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination
from .models import News, Category
from .serializers import NewsSerializer, CategorySerializer

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

