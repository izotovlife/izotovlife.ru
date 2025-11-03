# Путь: backend/urls.py
# Назначение: Корневой роутинг Django-проекта (sitemap.xml, robots.txt, API, JWT, соц.авторизация, медиа-миниатюры).
#
# Что важно по sitemap (Django 5.x):
#   • Индекс: /sitemap.xml  (index-вью)
#   • Секция: /sitemap-<section>.xml  (страницы через ?p=2, ?p=3...)
#   • index получает sitemap_url_name="sitemap-section", чтобы знать имя секционной вьюхи.
#   • НЕТ gzip-параметра у index/sitemap — его убрали в Django 5.x.
#
# Остальной функционал сохранён:
#   • Auth (dj-rest-auth / allauth), публичные совместимые whoami/users/me
#   • Похожие новости (универсальные + легаси)
#   • ✅ COMPAT избранного: /api/news/check/ и /api/news/toggle/
#   • ✅ Stub метрик: /api/news/metrics/hit/ (200 OK)
#   • ✅ Совместимый детальный путь: /api/article/<slug>/
#   • ⚠️ Порядок: compat-ручки (check/toggle/metrics) идут ВЫШЕ include("news.urls")

from importlib.util import find_spec

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page

from django.conf import settings
from django.conf.urls.static import static
from django.templatetags.static import static as static_url

# Sitemap views
from django.contrib.sitemaps.views import index as sitemap_index_view, sitemap as sitemap_section_view

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
from news.views_universal_detail import UniversalNewsDetailView

# ---- Карта для sitemap.xml ----
sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "articles": ArticleSitemap,
    "rss": ImportedNewsSitemap,
}

# ---- COMPAT избранного (чтобы старый фронт не падал на 404) ----
def favorites_check_compat_view(request):
    slug = request.GET.get("slug") or request.GET.get("id") or ""
    return JsonResponse({"ok": True, "slug": slug, "is_favorite": False}, status=200)

def favorites_toggle_compat_view(request):
    slug = request.POST.get("slug") or request.GET.get("slug") or ""
    u = getattr(request, "user", None)
    if not u or not u.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth_required", "slug": slug}, status=401)
    return JsonResponse({"ok": True, "slug": slug, "is_favorite": False}, status=200)

# ---- Stub метрик (200 ОК вместо 404) ----
@csrf_exempt
def metrics_hit_ok(request):
    if request.method == "POST":
        return JsonResponse({"ok": True})
    return JsonResponse({"detail": "Method not allowed"}, status=405)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Косметика логов / удобства разработки
    path(
        ".well-known/appspecific/com.chrome.devtools.json",
        RedirectView.as_view(
            url=static_url(".well-known/appspecific/com.chrome.devtools.json"),
            permanent=False,
        ),
        name="chrome-devtools-json",
    ),
    path(
        "favicon.ico",
        RedirectView.as_view(
            url=f"{settings.FRONTEND_BASE_URL.rstrip('/')}/favicon.ico",
            permanent=False,
        ),
        name="favicon-redirect",
    ),

    # --- Auth API (кастомные) ---
    path("api/auth/login/", LoginView.as_view(), name="api_login"),
    path("api/auth/me/", MeView.as_view(), name="api_me"),

    # --- Auth API (dj-rest-auth / allauth) ---
    path("api/auth/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/auth/social/", include("allauth.socialaccount.urls")),

    # --- Публичные совместимые аккаунты ---
    path("api/", include(("accounts.public_urls", "accounts_public"), namespace="accounts_public")),

    # --- Allauth web-формы ---
    path("accounts/", include("allauth.urls")),

    # --- Похожие новости (универсальный + легаси) ---
    path("api/news/related/<slug:slug>/", related_news, name="related_news"),
    path("api/news/article/<slug:slug>/related/", related_news_legacy_simple, name="related_news_article"),
    path("api/news/bez-kategorii/<slug:slug>/related/", related_news_legacy_simple, name="related_news_bez_kategorii"),
    path("api/news/rss/<slug:category>/<slug:slug>/related/", related_news_legacy_with_cat, name="related_news_rss_with_cat"),
    path("api/news/<slug:category>/<slug:slug>/related/", related_news_legacy_with_cat, name="related_news_with_cat"),

    # === ВАЖНО: COMPAT-ручки — ВЫШЕ include("news.urls") ===
    path("api/news/check/", favorites_check_compat_view, name="favorites_check_compat_root"),
    path("api/news/toggle/", favorites_toggle_compat_view, name="favorites_toggle_compat_root"),
    path("api/news/metrics/hit/", metrics_hit_ok, name="api_metrics_hit_stub"),

    # --- Основной роутер приложения news (реальные эндпоинты /api/news/...) ---
    path("api/", include(("news.urls", "news"), namespace="news")),

    # --- Совместимый старый путь детали статьи ---
    path("api/article/<slug:slug>/", UniversalNewsDetailView.as_view(), name="article_detail_compat"),

    # --- Короткий прямой путь для списка категорий ---
    path("api/categories/", CategoryListView.as_view(), name="categories_short"),

    # --- Security / Pages ---
    path("api/security/", include(("security.urls", "security"), namespace="security")),
    path("api/pages/", include(("pages.urls", "pages"), namespace="pages")),

    # --- Robots ---
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),

    # --- Sitemap INDEX + SECTION (cache=600; без gzip параметра) ---
    path(
        "sitemap.xml",
        cache_page(600)(sitemap_index_view),
        {
            "sitemaps": sitemaps,
            "sitemap_url_name": "sitemap-section",  # индекс знает имя секционной вьюхи
        },
        name="sitemap-index",
    ),
    path(
        # ВАЖНО: без "-<page>" — пагинация через ?p=2
        "sitemap-<section>.xml",
        cache_page(600)(sitemap_section_view),
        {"sitemaps": sitemaps},
        name="sitemap-section",
    ),
]

# Опционально: производительные эндпоинты News
if find_spec("news.urls_perf"):
    urlpatterns += [path("api/", include(("news.urls_perf", "news_perf"), namespace="news_perf"))]

# Опционально: прокси миниатюр / ресайзер
if find_spec("image_guard.urls"):
    urlpatterns += [path("api/media/", include(("image_guard.urls", "image_guard"), namespace="image_guard"))]

# Раздача медиа в DEV
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
