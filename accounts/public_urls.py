# Путь: accounts/public_urls.py
# Назначение: Публичные/совместимые пути под /api/ (без /auth в префиксе).

from django.urls import path
from .views_api import WhoAmIView, MeView, DashboardView

app_name = "accounts_public"

urlpatterns = [
    path("auth/whoami/", WhoAmIView.as_view(), name="auth-whoami"),          # /api/auth/whoami/
    path("users/me/", MeView.as_view(), name="users-me"),                    # /api/users/me/
    path("accounts/dashboard/", DashboardView.as_view(), name="dashboard"),  # /api/accounts/dashboard/
]
