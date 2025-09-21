# backend/security/urls.py
# Назначение: Маршруты для защищённого входа в админку.
# Путь: backend/security/urls.py

from django.urls import path
from . import views

app_name = "security"

urlpatterns = [
    # токен — строка (str), подходит для secrets.token_urlsafe()
    path("admin-entry/<str:token>/", views.admin_entrypoint, name="admin_entrypoint"),
    path("admin-session-login/", views.admin_session_login, name="admin_session_login"),
]




