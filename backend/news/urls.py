# ===== ФАЙЛ: backend/news/urls.py =====
# ПУТЬ: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\backend\news\urls.py
# НАЗНАЧЕНИЕ: Маршруты API для работы с новостями.
# ОПИСАНИЕ: Содержит публичные ленты, добавление авторских новостей и модерацию.

from django.urls import path
from .views import (
    NewsListView, CategoryListView, PopularNewsView,
    AuthorNewsCreateView, UserNewsListView,
    PendingNewsListView, ApproveNewsView,
)

urlpatterns = [
    path("", NewsListView.as_view(), name="news_list"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("popular/", PopularNewsView.as_view(), name="popular_news"),
    path("create/", AuthorNewsCreateView.as_view(), name="news_create"),
    path("mine/", UserNewsListView.as_view(), name="my_news"),
    path("pending/", PendingNewsListView.as_view(), name="pending_news"),
    path("<int:pk>/approve/", ApproveNewsView.as_view(), name="approve_news"),
]
