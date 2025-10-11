# Путь: backend/urls.py
# Назначение: Корневой роутинг Django-проекта (включая sitemap.xml, robots.txt, API, JWT и соц.авторизацию).

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

from news.views import CategoryListView  # ✅ добавили импорт, чтобы можно было отдать /api/categories/

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

    # --- Auth API (твои кастомные ручки) ---
    path("api/auth/login/", LoginView.as_view(), name="api_login"),
    path("api/auth/me/", MeView.as_view(), name="api_me"),

    # --- JWT + соц.авторизация через dj-rest-auth ---
    path("api/auth/", include("dj_rest_auth.urls")),                 # login/logout/password reset
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),  # регистрация
    path("api/auth/social/", include("allauth.socialaccount.urls")), # соцсети (VK, Яндекс, Google)

    # --- Allauth (стандартные урлы, если хочешь оставить web-формы) ---
    path("accounts/", include("allauth.urls")),

    # --- News ---
    path("api/", include(("news.urls", "news"), namespace="news")),

    # ✅ Прямой путь для категорий без /news/
    path("api/categories/", CategoryListView.as_view(), name="categories_short"),

    # --- Security (уникальная ссылка для админки) ---
    path("api/security/", include(("security.urls", "security"), namespace="security")),

    # --- Pages (статические страницы) ---
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

# ✅ Раздача медиафайлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
