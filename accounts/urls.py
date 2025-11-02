# Путь: backend/accounts/urls.py
# Назначение: URL-ы аутентификации (логин, регистрация, активация, восстановление пароля),
#             публичные страницы авторов и служебные совместимые эндпоинты для фронтенда.
#
# Обновления (ничего не удалено):
#   ✅ Добавлен маршрут повторной отправки письма активации: /resend-activation/
#   ✅ Добавлены BACK-COMPAT алиасы под старые эндпоинты:
#        - /registration/  -> на тот же RegisterView
#        - /registration/confirm/<uidb64>/<token>/ -> на тот же ActivateAccountView
#      Это сохранит совместимость с фронтендом, который может звать /api/auth/registration/…
#   ✅ ДОБАВЛЕНО для совместимости с фронтом:
#        - /auth/whoami/      → WhoAmIView (гость/пользователь)
#        - /users/me/         → alias к MeView (некоторые места фронта дергают именно этот путь)
#        - /accounts/dashboard/→ простая сводка профиля (чтобы не было 404 на странице автора/кабинета)
#
# Примечание о префиксах:
#   Этот файл обычно подключается в корневом urls.py под префиксом /api/:
#       path("api/", include("accounts.urls"))
#   Поэтому здесь НЕ используем /api/ в путях. В итоге получаются, например:
#       /api/login/, /api/register/, /api/auth/whoami/, /api/users/me/, /api/accounts/dashboard/ и т.д.

from django.urls import path

from .views import (
    LoginView,
    MeView,
    AuthorDetailView,
    RegisterView,
    ActivateAccountView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ResendActivationView,  # ✅ добавлено ранее
)

# Эти вьюхи мы держим отдельно (лёгкие JSON-ответы, совместимость с фронтом)
# Если вы разместили их в другом модуле — поправьте импорт на актуальный.
from .views_api import WhoAmIView, DashboardView  # ✅ добавлено

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # ===== Аутентификация =====
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),

    # Базовая информация о текущем пользователе
    path("me/", MeView.as_view(), name="me"),

    # ✅ Совместимость под фронт: /api/auth/whoami/
    path("auth/whoami/", WhoAmIView.as_view(), name="auth-whoami"),

    # ✅ Совместимость под фронт: /api/users/me/
    path("users/me/", MeView.as_view(), name="users-me"),

    # ✅ Совместимый "кабинет" (не 404)
    path("accounts/dashboard/", DashboardView.as_view(), name="accounts-dashboard"),

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
