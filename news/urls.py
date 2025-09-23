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
from .author_views import AuthorArticleViewSet
from .views_upload import upload_image
from . import editor_views   # ✅ редакторские ручки теперь тут

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
    path("editor/moderation-queue/", editor_views.ModerationQueueView.as_view(), name="editor_moderation_queue"),
    path("editor/review/<int:pk>/<str:action>/", editor_views.ReviewArticleView.as_view(), name="editor_review_article"),

    # загрузка изображений
    path("upload-image/", upload_image, name="upload_image"),

    # авторские статьи
    path("", include(router.urls)),
]
