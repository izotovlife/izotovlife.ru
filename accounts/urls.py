# backend/accounts/urls.py
# Назначение: URL-ы аутентификации и публичные страницы авторов.
# Путь: backend/accounts/urls.py

from django.urls import path
from .views import LoginView, MeView, account_redirect, AuthorDetailView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # API аутентификации
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", MeView.as_view(), name="me"),

    # Редирект аккаунта
    path("account-redirect/", account_redirect, name="account_redirect"),

    # Публичный профиль автора
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author_detail"),
]

