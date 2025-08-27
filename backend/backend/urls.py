# backend/backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # API endpoints
    path("api/accounts/", include("accounts.urls")),
    path("api/news/", include("news.urls")),

    # JWT авторизация
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

# Динамический или стандартный admin
if hasattr(settings, "DYNAMIC_ADMIN_URL"):
    urlpatterns.append(path(f"{settings.DYNAMIC_ADMIN_URL}/", admin.site.urls))
else:
    urlpatterns.append(path("admin/", admin.site.urls))

# Раздача медиа/статики в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
