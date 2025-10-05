# Путь: backend/news/urls.py
# Назначение: маршруты новостей (лента, категории, поиск, детали, похожие, метрики, резолверы).
# Обновления:
#   ✅ Исправлен порядок маршрутов: SEO-варианты article/rss идут ПЕРЕД старыми.
#   ✅ Исправлены маршруты для /related/.
#   ✅ Всё остальное без изменений.

# Путь: backend/news/urls.py
from django.urls import path, include, re_path
from django.http import HttpResponsePermanentRedirect
from rest_framework.routers import DefaultRouter
from . import api_extra_views
from .views import (
    CategoryListView,
    CategoryNewsView,
    NewsFeedView,
    NewsFeedImagesView,
    NewsFeedTextView,
    ArticleDetailView,
    SearchView,
    ImportedNewsDetailView,
    related_news,
    hit_metrics,
)
from .author_views import AuthorArticleViewSet
from .views_upload import upload_image
from . import editor_views

router = DefaultRouter()
router.register(r"author/articles", AuthorArticleViewSet, basename="author-articles")

app_name = "news"

urlpatterns = [
    # 📌 Категории
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("category/<slug:slug>/", CategoryNewsView.as_view(), name="category_news"),

    # 📌 Лента
    path("feed/", NewsFeedView.as_view(), name="news_feed"),
    path("feed/images/", NewsFeedImagesView.as_view(), name="news_feed_images"),
    path("feed/text/", NewsFeedTextView.as_view(), name="news_feed_text"),

    # 📌 ⚡ Быстрый автопоиск (должен быть до resolve и <slug:slug>)
    path("autocomplete/", api_extra_views.autocomplete_news, name="autocomplete_news"),

    # 📌 Поиск
    path("search/", SearchView.as_view(), name="search_all"),

    # 📌 Резолверы и чистый URL
    path("resolve/<slug:slug>/", api_extra_views.resolve_news, name="resolve_news"),
    path("by-slug/<slug:slug>/", api_extra_views.by_slug_redirect, name="by_slug_redirect"),

    # 📌 SEO-Детальные страницы
    path("article/<slug:category>/<slug:slug>/", ArticleDetailView.as_view(), name="article_detail_seo"),
    path("rss/source/<slug:source>/<slug:slug>/", ImportedNewsDetailView.as_view(), name="rss_detail_seo"),

    # 📌 Старый формат детальных страниц
    path("article/<slug:slug>/", ArticleDetailView.as_view(), name="article_detail"),
    path("rss/<slug:slug>/", ImportedNewsDetailView.as_view(), name="rss_detail"),

    # 📌 Метрики просмотров
    path("metrics/hit/", hit_metrics, name="hit_metrics"),

    # 📌 Редактор
    path("editor/moderation-queue/", editor_views.ModerationQueueView.as_view(), name="editor_moderation_queue"),
    path("editor/review/<int:pk>/<str:action>/", editor_views.ReviewArticleView.as_view(), name="editor_review_article"),

    # 📌 Загрузка изображений
    path("upload-image/", upload_image, name="upload_image"),

    # 📌 Авторские статьи (router)
    path("", include(router.urls)),

    # 📌 Ловец коротких slug (последним!)
    path("<slug:slug>/", api_extra_views.by_slug_redirect, name="news_by_slug"),
]

# 📌 SEO-маршруты похожих новостей
urlpatterns += [
    path("article/<slug:category>/<slug:slug>/related/", related_news, name="related_article_seo"),
    path("rss/source/<slug:source>/<slug:slug>/related/", related_news, name="related_rss_seo"),
    path("<str:type>/<slug:slug>/related/", related_news, name="related_news"),

    # 📌 Legacy-редиректы
    re_path(r"^imported/(?P<slug>source-[\w-]+)/$", lambda r, slug: HttpResponsePermanentRedirect(f"/api/news/rss/{slug}/")),
    re_path(r"^rss/(?P<slug>source-[\w-]+)/$", lambda r, slug: HttpResponsePermanentRedirect(f"/api/news/rss/{slug}/")),
]
