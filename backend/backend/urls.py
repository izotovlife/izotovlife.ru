# backend/backend/urls.py
# Путь: backend/backend/urls.py
# Назначение: корневые URL проекта, включая API и безопасный вход в админку.

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views_security import create_admin_link, use_admin_link, admin_logout

urlpatterns = [
    # API endpoints
    path("api/accounts/", include("accounts.urls")),
    path("api/news/", include("news.urls")),
    path("api/aggregator/", include("aggregator.urls")),

    # JWT авторизация
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Безопасная админка
    path("admin/link/", create_admin_link, name="admin_link"),
    path("admin/<str:token>/", use_admin_link, name="admin_use"),
    path("_internal_admin/", admin.site.urls),
    path("admin/logout/", admin_logout, name="admin_logout"),
]

# Раздача медиа/статики в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
