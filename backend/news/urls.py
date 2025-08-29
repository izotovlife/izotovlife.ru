# backend/news/urls.py
# Путь: backend/news/urls.py
# Назначение: маршруты API для работы с новостями.

from django.urls import path
from .views import (
    NewsListView,
    CategoryListView,
    CategorySubscribeView,
    CategoryUnsubscribeView,
    PopularNewsView,
    TopNewsView,
    NewsDetailView,
    NewsCreateView,
    NewsModerationListView,
    NewsApproveView,
)

urlpatterns = [
    path("", NewsListView.as_view(), name="news_list"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/<int:pk>/subscribe/", CategorySubscribeView.as_view(), name="category_subscribe"),
    path("categories/<int:pk>/unsubscribe/", CategoryUnsubscribeView.as_view(), name="category_unsubscribe"),
    path("popular/", PopularNewsView.as_view(), name="popular_news"),
    path("top/", TopNewsView.as_view(), name="top_news"),
    path("<int:pk>/", NewsDetailView.as_view(), name="news_detail"),
    path("create/", NewsCreateView.as_view(), name="news_create"),
    path("moderation/", NewsModerationListView.as_view(), name="news_moderation"),
    path("moderation/<int:pk>/approve/", NewsApproveView.as_view(), name="news_approve"),
]
