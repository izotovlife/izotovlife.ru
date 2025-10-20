# Путь: backend/urls.py
# Назначение: Корневой роутинг Django-проекта (sitemap.xml, robots.txt, API, JWT, соц.авторизация, медиа-миниатюры).
#
# Что сделано:
#   ✅ Сохранены все имеющиеся маршруты (auth, news, security, pages, sitemap/robots)
#   ✅ Ресайзер миниатюр доступен ровно по одному пути: /api/media/thumbnail/
#   ✅ ДОБАВЛЕНО: include('news.urls_perf') → быстрый батч-эндпоинт обложек категорий /api/categories/covers/
#   ✅ ДОБАВЛЕНО: маршруты social-complete и token/refresh (для соц-входа через allauth → SimpleJWT)
#   ✅ ДОБАВЛЕНО (безопасно): опциональные редиректы /accounts/login|signup → фронт (если есть файл accounts/views_redirects.py)
#   ✅ ДОБАВЛЕНО: include('news.urls_compat') → совместимость старых путей (например, /api/news/thumbnail/ → /api/media/thumbnail/)
#   🧹 В DEV (DEBUG=True) медиа-файлы раздаются локально через static().
#
# 🛠 УДАЛЕНО (обязательно для корректной работы):
#   — Дублирующийся импорт и финальный блок в самом низу, где заново создавался `urlpatterns = [...]`.
#     Он ЗАТИРАЛ все предыдущие маршруты. Теперь совместимость подключена правильно, без перезаписи списка.

from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from accounts.views import LoginView, MeView
from news.sitemaps import (
    StaticViewSitemap,
    CategorySitemap,
    ArticleSitemap,
    ImportedNewsSitemap,
)
from news.views import CategoryListView

# Эндпоинты «Похожие новости»
from news.api_related import (
    related_news,
    related_news_legacy_simple,
    related_news_legacy_with_cat,
)

from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenRefreshView

# Опциональные редиректы на фронт для /accounts/login и /accounts/signup (если файл есть).
try:
    from accounts.views_redirects import (
        FrontendLoginRedirectView,
        FrontendSignupRedirectView,
    )
    _HAS_FRONT_REDIRECTS = True
except Exception:
    _HAS_FRONT_REDIRECTS = False

# Карта для sitemap.xml
sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "articles": ArticleSitemap,
    "rss": ImportedNewsSitemap,
}

# ---- Основные URL-маршруты ----
urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth API (прямые кастомные вьюхи)
    path("api/auth/login/", LoginView.as_view(), name="api_login"),
    path("api/auth/me/", MeView.as_view(), name="api_me"),

    # Auth API (dj-rest-auth, allauth)
    path("api/auth/", include("accounts.urls")),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/auth/social/", include("allauth.socialaccount.urls")),
    path("api/auth/", include(("accounts.urls", "accounts"), namespace="accounts")),
]

# Перехватываем серверные /accounts/login и /accounts/signup и уводим на фронт (если вьюхи существуют)
if _HAS_FRONT_REDIRECTS:
    urlpatterns += [
        path("accounts/login/", FrontendLoginRedirectView.as_view(), name="accounts_login_redirect"),
        path("accounts/signup/", FrontendSignupRedirectView.as_view(), name="accounts_signup_redirect"),
    ]

# Allauth (web-формы)
urlpatterns += [
    path("accounts/", include("allauth.urls")),
]

# Похожие новости (универсальный + легаси-совместимость)
urlpatterns += [
    path("api/news/related/<slug:slug>/", related_news, name="related_news"),
    path("api/news/article/<slug:slug>/related/", related_news_legacy_simple, name="related_news_article"),
    path("api/news/bez-kategorii/<slug:slug>/related/", related_news_legacy_simple, name="related_news_bez_kategorii"),
    path("api/news/rss/<slug:category>/<slug:slug>/related/", related_news_legacy_with_cat, name="related_news_rss_with_cat"),
    path("api/news/<slug:category>/<slug:slug>/related/", related_news_legacy_with_cat, name="related_news_with_cat"),
]

# News (основной роутер приложения)
urlpatterns += [
    path("api/", include(("news.urls", "news"), namespace="news")),
    path("api/", include(("news.urls_perf", "news_perf"), namespace="news_perf")),  # батч-обложки категорий
    path("api/categories/", CategoryListView.as_view(), name="categories_short"),
]

# ✅ Совместимость старых путей (например, /api/news/thumbnail/ → новый медиаресайзер)
urlpatterns += [
    path("", include("news.urls_compat")),
]

# Security
urlpatterns += [
    path("api/security/", include(("security.urls", "security"), namespace="security")),
]

# Pages
urlpatterns += [
    path("api/pages/", include(("pages.urls", "pages"), namespace="pages")),
]

# Media (ресайзер миниатюр)
urlpatterns += [
    path("api/media/", include(("media.urls", "media"), namespace="media")),
]

# Robots / Sitemap
urlpatterns += [
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

# Завершение соц-логина и refresh токена
urlpatterns += [
    path("api/auth/social/", include("accounts.social_urls")),  # /api/auth/social/complete/
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# Раздача медиа в DEV
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
