# Путь: backend/accounts/urls.py
# Назначение: URL-ы аутентификации (логин, регистрация, активация, восстановление пароля) и публичные страницы авторов.
# Обновления (ничего не удалено):
#   ✅ Добавлен маршрут повторной отправки письма активации: /resend-activation/
#   ✅ Добавлены BACK-COMPAT алиасы под старые эндпоинты:
#        - /registration/  -> на тот же RegisterView
#        - /registration/confirm/<uidb64>/<token>/ -> на тот же ActivateAccountView
#      Это сохранит совместимость с фронтендом, который может звать /api/auth/registration/…
#   ✅ Все текущие маршруты login/refresh/me/register/activate/password-reset/* оставлены без изменений.

from django.urls import path
from .views import (
    LoginView,
    MeView,
    AuthorDetailView,
    RegisterView,
    ActivateAccountView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ResendActivationView,  # ✅ добавлено
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

    # ✅ Повторная отправка письма активации
    path("resend-activation/", ResendActivationView.as_view(), name="resend_activation"),

    # ✅ BACK-COMPAT алиасы под старые пути (/registration/…)
    path("registration/", RegisterView.as_view(), name="registration"),  # alias к register/
    path(
        "registration/confirm/<uidb64>/<token>/",
        ActivateAccountView.as_view(),
        name="registration_confirm",
    ),  # alias к activate/

    # ===== Восстановление пароля =====
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),

    # ===== Публичный профиль автора =====
    path("authors/<int:pk>/", AuthorDetailView.as_view(), name="author_detail"),
]
