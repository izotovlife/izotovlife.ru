# Путь: backend/news/urls.py
# Назначение: маршруты новостей без упоминания источников в адресах.
# Обновлено:
#   ✅ Статьи и RSS-новости открываются по /news/<slug>/ и /news/<slug>/related/
#   ✅ Категории остаются по /category/<slug>/
#   ✅ Старые пути /news/source/... и /news/rss/... редиректят на новый формат.

from django.urls import path, include, re_path
from django.http import HttpResponsePermanentRedirect
from rest_framework.routers import DefaultRouter

from .views_suggest import SuggestNewsView
from .views import (
    CategoryListView,
    CategoryNewsView,
    NewsFeedView,
    NewsFeedImagesView,
    NewsFeedTextView,
    ArticleDetailView,
    ImportedNewsDetailView,
    SearchView,
    SmartSearchViewEnhanced as SmartSearchView,
    related_news,
    HitMetricsView,
)
from .author_views import AuthorArticleViewSet
from .views_upload import upload_image
from . import editor_views
from . import api_extra_views
from .views_universal_detail import UniversalNewsDetailView

router = DefaultRouter()
router.register(r"author/articles", AuthorArticleViewSet, basename="author-articles")

app_name = "news"

urlpatterns = [
    # 📨 Форма «Предложить новость»
    path("suggest/", SuggestNewsView.as_view(), name="suggest-news"),

    # 📂 Категории
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("category/<slug:slug>/", CategoryNewsView.as_view(), name="category_news"),

    # 📰 Лента
    path("news/feed/", NewsFeedView.as_view(), name="news_feed"),
    path("news/feed/images/", NewsFeedImagesView.as_view(), name="news_feed_images"),
    path("news/feed/text/", NewsFeedTextView.as_view(), name="news_feed_text"),

    # 🔍 Поиск
    path("news/search/", SearchView.as_view(), name="search"),
    path("news/search/smart/", SmartSearchView.as_view(), name="smart_search"),

    # 📊 Метрики
    path("news/metrics/hit/", HitMetricsView.as_view(), name="metrics_hit"),

    # 🧩 Резолверы
    path("resolve/<slug:slug>/", api_extra_views.resolve_news, name="resolve_news"),

    # 🖼️ Загрузка изображений
    path("upload-image/", upload_image, name="upload_image"),

    # ✍️ Редактор
    path("editor/moderation-queue/", editor_views.ModerationQueueView.as_view(), name="editor_moderation_queue"),
    path("editor/review/<int:pk>/<str:action>/", editor_views.ReviewArticleView.as_view(), name="editor_review_article"),

    # 🧑‍💻 Авторские статьи
    path("", include(router.urls)),

    # 🔁 Старые пути редиректим на новый формат
    re_path(r"^news/source/(?P<source>[\w-]+)/(?P<slug>[\w-]+)/$", lambda r, source, slug:
            HttpResponsePermanentRedirect(f"/api/news/{slug}/")),
    re_path(r"^news/rss/(?P<source>[\w-]+)/(?P<slug>[\w-]+)/$", lambda r, source, slug:
            HttpResponsePermanentRedirect(f"/api/news/{slug}/")),

    # ✅ Похожие новости по короткому пути /news/<slug>/related/
    path("news/<slug:slug>/related/", related_news, name="related_universal"),

    # ✅ Универсальный SEO-путь для детальной новости /news/<slug>/
    path("news/<slug:slug>/", UniversalNewsDetailView.as_view(), name="universal_detail"),
]
