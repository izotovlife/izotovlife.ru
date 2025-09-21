# backend/urls.py
# Назначение: Корневой роутинг Django-проекта (включая sitemap.xml и robots.txt).
# Путь: backend/urls.py

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
    path("admin/", admin.site.urls),

    # --- Auth API ---
    path("api/auth/login/", LoginView.as_view(), name="api_login"),
    path("api/auth/me/", MeView.as_view(), name="api_me"),

    # --- News ---
    path("api/news/", include(("news.urls", "news"), namespace="news")),

    # --- Security (уникальная ссылка для админки) ---
    path("api/security/", include(("security.urls", "security"), namespace="security")),

    # --- Security (Статические страницы для админки) ---
    path("api/pages/", include(("pages.urls", "pages"), namespace="pages")),

    # --- Robots / Sitemap ---
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
]

# ✅ Раздача медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
