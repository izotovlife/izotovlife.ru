# backend/news/urls.py
# Назначение: Маршруты новостей: лента, категории, поиск, статьи, авторский CRUD, RSS-деталь, загрузка изображений.
# Путь: backend/news/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryListView,
    CategoryNewsView,
    NewsFeedView,
    NewsFeedImagesView,
    NewsFeedTextView,
    ArticleDetailView,
    SearchView,
    ImportedNewsDetailView,
)
from .author_views import AuthorArticleViewSet, moderation_queue, review_article
from .views_upload import upload_image   # ✅ добавляем загрузку изображений

router = DefaultRouter()
router.register(r'author/articles', AuthorArticleViewSet, basename='author-articles')

app_name = "news"

urlpatterns = [
    # категории
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("category/<slug:slug>/", CategoryNewsView.as_view(), name="category_news"),

    # лента
    path("feed/", NewsFeedView.as_view(), name="news_feed"),
    path("feed/images/", NewsFeedImagesView.as_view(), name="news_feed_images"),
    path("feed/text/", NewsFeedTextView.as_view(), name="news_feed_text"),

    # поиск
    path("search/", SearchView.as_view(), name="search_all"),

    # детали
    path("article/<slug:slug>/", ArticleDetailView.as_view(), name="article_detail"),
    path("rss/<int:id>/", ImportedNewsDetailView.as_view(), name="rss_detail"),

    # редактор
    path("author/moderation-queue/", moderation_queue, name="moderation_queue"),
    path("author/review/<int:pk>/<str:action>/", review_article, name="review_article"),

    # загрузка изображений из редактора Quill
    path("upload-image/", upload_image, name="upload_image"),

    # авторские статьи
    path("", include(router.urls)),
]
