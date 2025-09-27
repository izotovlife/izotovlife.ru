# backend/accounts/urls.py
# Назначение: URL-ы аутентификации (логин, регистрация, активация, восстановление пароля) и публичные страницы авторов.
# Путь: backend/accounts/urls.py

from django.urls import path
from .views import (
    LoginView,
    MeView,
    AuthorDetailView,
    RegisterView,
    ActivateAccountView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # ===== Аутентификация =====
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", MeView.as_view(), name="me"),

    # ===== Регистрация и активация =====
    path("register/", RegisterView.as_view(), name="register"),
    path("activate/<uidb64>/<token>/", ActivateAccountView.as_view(), name="activate"),

    # ===== Восстановление пароля =====
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password-reset-confirm/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),

    # ===== Публичный профиль автора =====
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author_detail"),
]



