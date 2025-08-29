# backend/news/views.py
# Путь: backend/news/views.py
# Назначение: API-представления для работы с новостями и категориями.

from datetime import timedelta

from django.db.models import F
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from accounts.models import Subscription
from .models import News, Category
from .serializers import NewsSerializer, CategorySerializer, NewsCreateSerializer

class NewsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50

class NewsListView(generics.ListAPIView):
    queryset = (
        News.objects.filter(is_moderated=True)
        .select_related("author", "category")
        .order_by("-created_at")
    )
    serializer_class = NewsSerializer
    pagination_class = NewsPagination
    permission_classes = [permissions.AllowAny]

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class CategorySubscribeView(generics.GenericAPIView):
    """Подписка пользователя на категорию."""

    queryset = Category.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        category = self.get_object()
        Subscription.objects.get_or_create(user=request.user, category=category)
        return Response({"detail": "subscribed"}, status=status.HTTP_201_CREATED)


class CategoryUnsubscribeView(generics.GenericAPIView):
    """Отписка пользователя от категории."""

    queryset = Category.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        category = self.get_object()
        Subscription.objects.filter(user=request.user, category=category).delete()
        return Response({"detail": "unsubscribed"}, status=status.HTTP_200_OK)

class PopularNewsView(generics.ListAPIView):
    queryset = (
        News.objects.filter(is_moderated=True)
        .select_related("author", "category")
        .order_by("-id")[:10]
    )
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]


class TopNewsView(generics.ListAPIView):
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        period = self.request.query_params.get("period", "day")
        now = timezone.now()
        delta = timedelta(days=7) if period == "week" else timedelta(days=1)
        start = now - delta
        return (
            News.objects.filter(is_moderated=True, created_at__gte=start)
            .select_related("author", "category")
            .order_by("-views_count")[:10]
        )


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

    queryset = (
        News.objects.filter(is_moderated=False)
        .select_related("author", "category")
    )
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


class NewsDetailView(generics.RetrieveAPIView):
    """Детальный просмотр новости с безопасным подсчётом просмотров."""

    queryset = News.objects.select_related("author", "category")
    serializer_class = NewsSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        News.objects.filter(pk=instance.pk).update(views_count=F("views_count") + 1)
        instance.refresh_from_db(fields=["views_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

