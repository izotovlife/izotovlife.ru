# ===== ФАЙЛ: backend/backend/urls.py =====
# ПУТЬ: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\backend\backend\urls.py
# НАЗНАЧЕНИЕ: Центральный URL-конфиг проекта. Подключает API и логин в админку по одноразовой ссылке.
# ОПИСАНИЕ: Админ-панель недоступна по стандартному пути. Суперпользователь отправляет POST /admin/login/,
#           получает ссылку /admin/<token>/ и далее перенаправляется во внутренний путь /_internal_admin/.

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views_security import admin_login, use_admin_link, admin_logout

urlpatterns = [
    # API endpoints
    path("api/accounts/", include("accounts.urls")),
    path("api/news/", include("news.urls")),

    # JWT авторизация
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Безопасная админка
    path("admin/login/", admin_login, name="admin_login"),
    path("admin/<str:token>/", use_admin_link, name="admin_use_link"),
    path("admin/logout/", admin_logout, name="admin_logout"),
    path("_internal_admin/", admin.site.urls),
]

# Раздача медиа/статики в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
