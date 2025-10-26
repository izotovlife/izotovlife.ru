# Путь: backend/urls.py
# Назначение: Корневой роутинг Django-проекта (sitemap.xml, robots.txt, API, JWT, соц.авторизация, медиа-миниатюры).
# Особенности:
#   • Без дубля "accounts.urls"
#   • "news.urls_perf" и "image_guard.urls" подключаются, только если реально существуют
#   • В DEV медиа раздаются через static()

from importlib.util import find_spec

from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from django.conf import settings
from django.conf.urls.static import static

from accounts.views import LoginView, MeView
from news.sitemaps import (
    StaticViewSitemap,
    CategorySitemap,
    ArticleSitemap,
    ImportedNewsSitemap,
)
from news.views import CategoryListView
from news.api_related import (
    related_news,
    related_news_legacy_simple,
    related_news_legacy_with_cat,
)

# ---- Карта для sitemap.xml ----
sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "articles": ArticleSitemap,
    "rss": ImportedNewsSitemap,
}

# ---- Основные URL-маршруты ----
urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Auth API (прямые кастомные вьюхи) ---
    path("api/auth/login/", LoginView.as_view(), name="api_login"),
    path("api/auth/me/", MeView.as_view(), name="api_me"),

    # --- Auth API (dj-rest-auth, allauth, локальные аккаунты) ---
    # Подключаем локальные аккаунт-маршруты ОДИН раз, под пространством имён
    path("api/auth/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/auth/social/", include("allauth.socialaccount.urls")),

    # --- Allauth (web-формы) ---
    path("accounts/", include("allauth.urls")),

    # --- Похожие новости (универсальный + легаси-совместимость) ---
    path("api/news/related/<slug:slug>/", related_news, name="related_news"),
    path("api/news/article/<slug:slug>/related/", related_news_legacy_simple, name="related_news_article"),
    path("api/news/bez-kategorii/<slug:slug>/related/", related_news_legacy_simple, name="related_news_bez_kategorii"),
    path("api/news/rss/<slug:category>/<slug:slug>/related/", related_news_legacy_with_cat, name="related_news_rss_with_cat"),
    path("api/news/<slug:category>/<slug:slug>/related/", related_news_legacy_with_cat, name="related_news_with_cat"),

    # --- News (основной роутер приложения) ---
    path("api/", include(("news.urls", "news"), namespace="news")),

    # --- Короткий прямой путь для списка категорий ---
    path("api/categories/", CategoryListView.as_view(), name="categories_short"),

    # --- Security ---
    path("api/security/", include(("security.urls", "security"), namespace="security")),

    # --- Pages ---
    path("api/pages/", include(("pages.urls", "pages"), namespace="pages")),

    # --- Robots / Sitemap ---
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

# --- Опционально: производительные эндпоинты News (подключаем, только если модуль есть) ---
if find_spec("news.urls_perf"):
    urlpatterns += [path("api/", include(("news.urls_perf", "news_perf"), namespace="news_perf"))]

# --- Опционально: ресайзер/прокси миниатюр (если есть приложение image_guard и его urls) ---
if find_spec("image_guard.urls"):
    urlpatterns += [path("api/media/", include(("image_guard.urls", "image_guard"), namespace="image_guard"))]

# ---- Раздача медиа в DEV ----
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
