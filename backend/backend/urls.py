# backend/backend/urls.py
# Назначение: корневые URL проекта, включая API и безопасный вход в админку.

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin   # <-- добавляем

# теперь берём функции из security.views
from security.views import create_admin_link, use_admin_link, admin_logout
from aggregator.admin import custom_admin_site   # ✅ импортируем готовый экземпляр

urlpatterns = [
    # API endpoints
    path("api/accounts/", include("accounts.urls")),
    path("api/news/", include("news.urls")),
    path("api/aggregator/", include("aggregator.urls")),

    # JWT авторизация
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Безопасная админка (одноразовые ссылки)
    path("admin/link/", create_admin_link, name="admin_link"),
    path("admin/<str:token>/", use_admin_link, name="admin_use"),
    path("admin/logout/", admin_logout, name="admin_logout"),

    # Кастомная админка (одноразовые ссылки + кнопка Fetch feeds)
    path("admin/", custom_admin_site.urls),

    # Стандартная админка Django (форма входа)
    path("dj-admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
