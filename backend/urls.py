# Путь: backend/urls.py
# Назначение: Корневой роутинг Django-проекта (sitemap.xml, robots.txt, API, JWT/соц-авторизация, закрытая админка).
# Важно:
#   • Настоящая админка публикуется ТОЛЬКО по /_internal_admin/
#   • Пакет security перехватывает /admin/ (404) и обрабатывает /admin/<token>/ для одноразового входа
#   • Все существующие API-маршруты сохранены
#   • Подключены совместимые RSS-маршруты news.urls_rss_compat

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

from django.conf import settings
from django.conf.urls.static import static

sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "articles": ArticleSitemap,
    "rss": ImportedNewsSitemap,
}

urlpatterns = [
    # --- Security (одноразовый вход и блокировка прямого /admin/) ---
    path("", include("security.urls")),

    # --- Auth API (ваши кастомные ручки) ---
    path("api/auth/login/", LoginView.as_view(), name="api_login"),
    path("api/auth/me/", MeView.as_view(), name="api_me"),

    # --- JWT + соц.авторизация через dj-rest-auth ---
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/auth/social/", include("allauth.socialaccount.urls")),

    # --- Allauth (стандартные веб-страницы, если нужны) ---
    path("accounts/", include("allauth.urls")),

    # --- News (основные маршруты) ---
    path("api/news/", include(("news.urls", "news"), namespace="news")),

    # 🆕 Совместимые RSS-маршруты под фронтовые пути:
    path(
        "api/news/",
        include(("news.urls_rss_compat", "news_rss_compat"), namespace="news_rss_compat"),
    ),

    # --- Pages (статические страницы) ---
    path("api/pages/", include(("pages.urls", "pages"), namespace="pages")),

    # --- CKEditor 5 uploads ---
    path("ckeditor5/", include("django_ckeditor_5.urls")),

    # --- Robots / Sitemap ---
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),

    # --- Django Admin (реальная админка ТОЛЬКО по закрытому пути) ---
    path("_internal_admin/", admin.site.urls),
]

# ✅ Раздача медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
