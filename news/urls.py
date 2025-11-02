# Путь: backend/news/urls.py
# Назначение: маршруты новостей без упоминания источников в адресах.
# Особенности:
#   ✅ Правильный префикс для API (без /api/ внутри — префикс добавляется на уровне проекта)
#   ✅ Универсальный детальный путь
#   ✅ Форма "Предложить новость" по /api/news/suggest/
#   ✅ Резолвер на /api/news/resolve/<slug>/
#   ✅ Эндпоинт ресайзера: /api/media/thumbnail/  (исправлено описание: не /api/news/media)
#   ✅ Батч-эндпоинт обложек категорий: /api/categories/covers/ (быстро!)
#   ✅ Мягкие редиректы со старых путей:
#        /api/news/<category>/<slug>/            → /api/news/<slug>/
#        /api/news/article/<category>/<slug>/    → /api/news/<slug>/
#        .../related/                            → /api/news/<slug>/related/
#   ✅ Маршрут умного поиска /api/news/search/smart/
#   ✅ Избранное читателя: /api/news/favorites/ (+ совместимые заглушки /news/check/ и /news/toggle/)
#   ✅ Алиасы слагов (obschestvo→obshchestvo, lenta-novostej→lenta-novostey, proisshestvija→proisshestviya)
#   ✅ Редиректы-алиасы сохраняют query string (?page=..., ?limit=...)
#   ✅ Совместимый маршрут /api/news/category/<slug>/ → CategoryNewsView
#   ✅ Совместимый набор /api/news/articles/ → AuthorArticleViewSet

from django.urls import path, include, re_path
from django.http import HttpResponsePermanentRedirect, JsonResponse
from rest_framework.routers import DefaultRouter

from .views_suggest import SuggestNewsView
from .views import (
    CategoryListView,
    CategoryNewsView,
    NewsFeedView,
    NewsFeedImagesView,
    NewsFeedTextView,
    ArticleDetailView,          # сохранён импорт (совместимость с другими местами)
    ImportedNewsDetailView,     # сохранён импорт
    SearchView,
    SmartSearchViewEnhanced,    # /news/search/smart/
    HitMetricsView,
)
# ⬇️ ВАЖНО: related_news берём из tolerant-вьюхи
from .views_related import related_news

from .author_views import AuthorArticleViewSet
from .views_upload import upload_image
from . import editor_views
from . import api_extra_views
from .views_universal_detail import UniversalNewsDetailView
from .views_media import thumbnail_proxy

# Батч-обложки категорий
from .api.category_covers import CategoryCoversView  # noqa: E402

# Совместимость: оставляем только нужные обёртки (без related_news_compat)
from .views_compat import (
    category_or_article_compat,
    HitMetricsCompatView,
    upload_image_compat,
)

# -------------------- Вспомогательное: редирект с сохранением query-string --------------------
def _redir_preserve_qs(request, new_path: str):
    """
    Возвращает 301-редирект на new_path, сохраняя query-string (?page=..., ?limit=...).
    new_path должен быть абсолютным путем (например, '/api/news/obshchestvo/').
    """
    qs = request.META.get("QUERY_STRING")
    if qs:
        return HttpResponsePermanentRedirect(f"{new_path}?{qs}")
    return HttpResponsePermanentRedirect(new_path)

# -------------------- ЛЕГАСИ-ЗАГЛУШКИ ДЛЯ ИЗБРАННОГО --------------------
# Эти две вьюхи нужны, чтобы старые адреса /api/news/check|toggle/ не давали 404.
# Они НЕ меняют БД. Как только подключишь настоящие ручки /api/news/favorites/check|toggle/,
# эти заглушки можно заменить на 301-редиректы.

def favorites_check_legacy(request):
    """
    GET /api/news/check/?slug=<slug>
    Возвращает безопасный ответ, чтобы UI не ломался.
    Для гостя: is_favorite = False.
    Для авторизованного сейчас тоже False (заглушка).
    """
    slug = request.GET.get("slug") or request.GET.get("id") or ""
    # Можно попытаться понять из сессии, но без модели избранного — всегда False.
    return JsonResponse({"ok": True, "slug": slug, "is_favorite": False}, status=200)

def favorites_toggle_legacy(request):
    """
    POST/GET /api/news/toggle/?slug=<slug>
    Заглушка: не меняет состояние, только сообщает, что нужен реальный backend избранного.
    Для неавторизованных — 401 (как ожидает большинство фронтов).
    """
    slug = request.POST.get("slug") or request.GET.get("slug") or ""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth_required", "slug": slug}, status=401)
    # Для авторизованных отвечаем стабильно, не меняя БД:
    return JsonResponse(
        {
            "ok": True,
            "slug": slug,
            "is_favorite": False,  # оставляем как есть, чтобы UI не мигал
            "message": "compat_stub: подключите /api/news/favorites/toggle/ для реального изменения",
        },
        status=200,
    )

# -------------------- Роутеры --------------------
router = DefaultRouter()
router.register(r"author/articles", AuthorArticleViewSet, basename="author-articles")

# Совместимый набор: /api/news/articles/ (для виджета автора)
router_news_prefix = DefaultRouter()
router_news_prefix.register(r"news/articles", AuthorArticleViewSet, basename="author-articles-compat")

app_name = "news"

urlpatterns = [
    # -------------------- Форма «Предложить новость» --------------------
    path("news/suggest/", SuggestNewsView.as_view(), name="suggest-news"),

    # -------------------- Категории --------------------
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("categories/covers/", CategoryCoversView.as_view(), name="category-covers"),  # быстрый батч
    path("category/<slug:slug>/", CategoryNewsView.as_view(), name="category_news"),

    # ✅ Совместимый маршрут под фронт: /api/news/category/<slug>/ → та же вьюха
    path("news/category/<slug:slug>/", CategoryNewsView.as_view(), name="category_news_compat"),

    # -------------------- Лента новостей --------------------
    path("news/feed/", NewsFeedView.as_view(), name="news_feed"),
    path("news/feed/images/", NewsFeedImagesView.as_view(), name="news_feed_images"),
    path("news/feed/text/", NewsFeedTextView.as_view(), name="news_feed_text"),

    # -------------------- Поиск --------------------
    path("news/search/", SearchView.as_view(), name="search"),
    path("news/search/smart/", SmartSearchViewEnhanced.as_view(), name="smart_search"),

    # -------------------- Метрики --------------------
    path("news/metrics/hit/", HitMetricsView.as_view(), name="metrics_hit"),
    # Совместимый GET-алиас
    path("news/hit/", HitMetricsCompatView.as_view(), name="hit_compat"),

    # -------------------- Резолвер --------------------
    path("news/resolve/<slug:slug>/", api_extra_views.resolve_news, name="resolve_news"),

    # -------------------- Загрузка изображений --------------------
    path("upload-image/", upload_image, name="upload_image"),
    # Совместимый алиас старого пути
    path("news/upload/", upload_image_compat, name="upload_image_compat"),

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
    path("", include(router.urls)),              # /api/author/articles/
    path("", include(router_news_prefix.urls)),  # /api/news/articles/  ← совместимость

    # -------------------- Совместимость (ДОЛЖНА БЫТЬ ВЫШЕ детальных путей) --------------------
    # 1) Старый вызов related БЕЗ slug в PATH — направляем на tolerant-вьюху (slug/id через query).
    path("news/related/", related_news, name="news_related"),

    # 2) /news/<slug>/?limit=.. → категория; иначе → универсальная детальная
    re_path(r"^news/(?P<slug>[-\w]+)/$", category_or_article_compat, name="news_cat_or_article"),

    # 3) ✅ Легаси-избранное (убирает 404 на детальной):
    path("news/check/",  favorites_check_legacy,  name="favorites_check_compat"),
    path("news/toggle/", favorites_toggle_legacy, name="favorites_toggle_compat"),

    # -------------------- Старые пути (редиректы с источниками) --------------------
    re_path(
        r"^news/source/(?P<source>[\w-]+)/(?P<slug>[\w-]+)/$",
        lambda r, source, slug: HttpResponsePermanentRedirect(f"/api/news/{slug}/")
    ),
    re_path(
        r"^news/rss/(?P<source>[\w-]+)/(?P<slug>[\w-]+)/$",
        lambda r, source, slug: HttpResponsePermanentRedirect(f"/api/news/{slug}/")
    ),

    # -------------------- Старые пути (категория в URL) --------------------
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

    # -------------------- Синонимы слагов (алиасы) --------------------
    # NB: Эти правила — ДО универсальных детальных путей, чтобы они сработали раньше.
    path("category/obschestvo/",     CategoryNewsView.as_view(), {"slug": "obshchestvo"},     name="category_alias_obschestvo"),
    path("category/lenta-novostej/", CategoryNewsView.as_view(), {"slug": "lenta-novostey"},  name="category_alias_lenta"),
    path("category/proisshestvija/", CategoryNewsView.as_view(), {"slug": "proisshestviya"},  name="category_alias_proissh"),

    path("news/category/obschestvo/",     CategoryNewsView.as_view(), {"slug": "obshchestvo"},    name="news_category_alias_obschestvo"),
    path("news/category/lenta-novostej/", CategoryNewsView.as_view(), {"slug": "lenta-novostey"}, name="news_category_alias_lenta"),
    path("news/category/proisshestvija/", CategoryNewsView.as_view(), {"slug": "proisshestviya"}, name="news_category_alias_proissh"),

    re_path(r"^news/obschestvo/$",             lambda r: _redir_preserve_qs(r, "/api/news/obshchestvo/"),            name="news_alias_obschestvo"),
    re_path(r"^news/lenta-novostej/$",         lambda r: _redir_preserve_qs(r, "/api/news/lenta-novostey/"),         name="news_alias_lenta"),
    re_path(r"^news/proisshestvija/$",         lambda r: _redir_preserve_qs(r, "/api/news/proisshestviya/"),         name="news_alias_proissh"),
    re_path(r"^news/обschestvo/related/$",     lambda r: _redir_preserve_qs(r, "/api/news/obshchestvo/related/"),    name="news_alias_obschestvo_related"),
    re_path(r"^news/lenta-novostej/related/$", lambda r: _redir_preserve_qs(r, "/api/news/lenta-novostey/related/"), name="news_alias_lenta_related"),
    re_path(r"^news/proisshestvija/related/$", lambda r: _redir_preserve_qs(r, "/api/news/proisshestviya/related/"), name="news_alias_proissh_related"),

    # -------------------- Похожие новости (корректный путь со slug в PATH) --------------------
    path("news/<slug:slug>/related/", related_news, name="related_universal"),

    # -------------------- Универсальный детальный путь --------------------
    # NB: До него уже стоит совместимый re_path, который сам решит: категория или деталка.
    path("news/<slug:slug>/", UniversalNewsDetailView.as_view(), name="universal_detail"),

    # -------------------- Ресайзер --------------------
    path("media/thumbnail/", thumbnail_proxy, name="media-thumbnail"),
]
