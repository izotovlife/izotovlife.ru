# backend/news/urls.py
from django.urls import path
from .views import NewsListView, CategoryListView, PopularNewsView

urlpatterns = [
    path("", NewsListView.as_view(), name="news_list"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("popular/", PopularNewsView.as_view(), name="popular_news"),
]
