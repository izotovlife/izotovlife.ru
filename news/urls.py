# Путь: backend/news/urls.py
# Назначение: маршруты новостей без упоминания источников в адресах.
# Особенности:
#   ✅ Правильный префикс для API (без /api/ внутри)
#   ✅ Универсальный детальный путь
#   ✅ Форма "Предложить новость" по /api/news/suggest/
#   ✅ Резолвер на /api/news/resolve/<slug>/
#   ✅ Эндпоинт ресайзера: /api/news/media/thumbnail/
#   ✅ Батч-эндпоинт обложек категорий: /api/categories/covers/ (быстро!)
#   ✅ ДОБАВЛЕНО: мягкие редиректы со старых путей:
#        /api/news/<category>/<slug>/            → /api/news/<slug>/
#        /api/news/article/<category>/<slug>/    → /api/news/<slug>/
#        .../related/                            → /api/news/<slug>/related/
#   ✅ ДОБАВЛЕНО: маршрут умного поиска /api/news/search/smart/

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
    SmartSearchViewEnhanced,  # ← ДОБАВЛЕНО: для /news/search/smart/
    related_news,
    HitMetricsView,
)
from .author_views import AuthorArticleViewSet
from .views_upload import upload_image
from . import editor_views
from . import api_extra_views
from .views_universal_detail import UniversalNewsDetailView
from .views_media import thumbnail_proxy

# Батч-обложки категорий
from .api.category_covers import CategoryCoversView  # noqa: E402

# -------------------- Роутер для авторских статей --------------------
router = DefaultRouter()
router.register(r"author/articles", AuthorArticleViewSet, basename="author-articles")

app_name = "news"

urlpatterns = [
    # -------------------- Форма «Предложить новость» --------------------
    path("news/suggest/", SuggestNewsView.as_view(), name="suggest-news"),

    # -------------------- Категории --------------------
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/covers/", CategoryCoversView.as_view(), name="category-covers"),  # быстрый батч
    path("category/<slug:slug>/", CategoryNewsView.as_view(), name="category_news"),

    # -------------------- Лента новостей --------------------
    path("news/feed/", NewsFeedView.as_view(), name="news_feed"),
    path("news/feed/images/", NewsFeedImagesView.as_view(), name="news_feed_images"),
    path("news/feed/text/", NewsFeedTextView.as_view(), name="news_feed_text"),

    # -------------------- Поиск --------------------
    path("news/search/", SearchView.as_view(), name="search"),
    path("news/search/smart/", SmartSearchViewEnhanced.as_view(), name="smart_search"),  # ← ДОБАВЛЕНО

    # -------------------- Метрики --------------------
    path("news/metrics/hit/", HitMetricsView.as_view(), name="metrics_hit"),

    # -------------------- Резолвер --------------------
    path("news/resolve/<slug:slug>/", api_extra_views.resolve_news, name="resolve_news"),

    # -------------------- Загрузка изображений --------------------
    path("upload-image/", upload_image, name="upload_image"),

    # -------------------- Редактор --------------------
    path(
        "editor/moderation-queue/",
        editor_views.ModerationQueueView.as_view(),
        name="editor_moderation_queue"
    ),
    path(
        "editor/review/<int:pk>/<str:action>/",
        editor_views.ReviewArticleView.as_view(),
        name="editor_review_article"
    ),

    # -------------------- Авторские статьи --------------------
    path("", include(router.urls)),

    # -------------------- Старые пути (редиректы с источниками) --------------------
    re_path(
        r"^news/source/(?P<source>[\w-]+)/(?P<slug>[\w-]+)/$",
        lambda r, source, slug: HttpResponsePermanentRedirect(f"/api/news/{slug}/")
    ),
    re_path(
        r"^news/rss/(?P<source>[\w-]+)/(?P<slug>[\w-]+)/$",
        lambda r, source, slug: HttpResponsePermanentRedirect(f"/api/news/{slug}/")
    ),

    # -------------------- ДОБАВЛЕНО: Старые пути (категория в URL) --------------------
    # Детальная
    re_path(
        r"^news/article/(?P<category>[\w-]+)/(?P<slug>[\w-]+)/$",
        lambda r, category, slug: HttpResponsePermanentRedirect(f"/api/news/{slug}/")
    ),
    re_path(
        r"^news/(?P<category>[\w-]+)/(?P<slug>[\w-]+)/$",
        lambda r, category, slug: HttpResponsePermanentRedirect(f"/api/news/{slug}/")
    ),
    # Похожие
    re_path(
        r"^news/article/(?P<category>[\w-]+)/(?P<slug>[\w-]+)/related/$",
        lambda r, category, slug: HttpResponsePermanentRedirect(f"/api/news/{slug}/related/")
    ),
    re_path(
        r"^news/(?P<category>[\w-]+)/(?P<slug>[\w-]+)/related/$",
        lambda r, category, slug: HttpResponsePermanentRedirect(f"/api/news/{slug}/related/")
    ),

    # -------------------- Похожие новости --------------------
    path("news/<slug:slug>/related/", related_news, name="related_universal"),

    # -------------------- Универсальный детальный путь --------------------
    path("news/<slug:slug>/", UniversalNewsDetailView.as_view(), name="universal_detail"),

    # -------------------- Ресайзер --------------------
    path("media/thumbnail/", thumbnail_proxy, name="media-thumbnail"),
]

# Комментарий:
#   Теперь любые старые обращения вида /api/news/article/<cat>/<slug>/ и /api/news/<cat>/<slug>/
#   автоматически переедут на /api/news/<slug>/ (и аналогично для /related/).
#   Умный поиск доступен по /api/news/search/smart/.
