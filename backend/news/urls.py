# backend/news/urls.py
# Путь: backend/news/urls.py
# Назначение: маршруты API для работы с новостями.

from django.urls import path
from .views import (
    NewsListView,
    CategoryListView,
    PopularNewsView,
    NewsCreateView,
    NewsModerationListView,
    NewsApproveView,
    FavoriteListView,
    FavoriteView,
)

urlpatterns = [
    path("", NewsListView.as_view(), name="news_list"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("popular/", PopularNewsView.as_view(), name="popular_news"),
    path("create/", NewsCreateView.as_view(), name="news_create"),
    path("moderation/", NewsModerationListView.as_view(), name="news_moderation"),
    path("moderation/<int:pk>/approve/", NewsApproveView.as_view(), name="news_approve"),
    path("favorites/", FavoriteListView.as_view(), name="favorite_list"),
    path("favorites/<int:news_id>/", FavoriteView.as_view(), name="favorite_detail"),
]
