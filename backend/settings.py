# backend/settings.py
# Назначение: Базовые настройки Django-проекта, PostgreSQL через .env, DRF, CORS, JWT,
# кастомная модель пользователя, защита админки + robots.txt support + email + соц.авторизация (VK, Yandex, Google).
# Путь: backend/settings.py

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем переменные окружения
load_dotenv(BASE_DIR / ".env")

# =======================
# БАЗОВЫЕ НАСТРОЙКИ
# =======================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Хосты и CSRF
if DEBUG:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
    CSRF_TRUSTED_ORIGINS = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
else:
    ALLOWED_HOSTS = ["izotovlife.ru", "www.izotovlife.ru"]
    CSRF_TRUSTED_ORIGINS = [
        "https://izotovlife.ru",
        "https://www.izotovlife.ru",
    ]

# =======================
# ПРИЛОЖЕНИЯ
# =======================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # third-party
    "rest_framework",
    "corsheaders",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "rest_framework.authtoken",   # ✅ для dj-rest-auth

    # --- соц. авторизация ---
    "allauth",
    "allauth.account",
    "allauth.socialaccount",

    # провайдеры соцсетей
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.vk",
    "allauth.socialaccount.providers.yandex",

    # dj-rest-auth
    "dj_rest_auth",
    "dj_rest_auth.registration",

    # local apps
    "accounts",
    "news.apps.NewsConfig",
    "moderation",
    "security",
    "rssfeed",
    "pages",
    "ckeditor",
]

# =======================
# MIDDLEWARE
# =======================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "security.middleware.AdminInternalGateMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "backend.urls"

# =======================
# TEMPLATES
# =======================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "backend" / "templates"],  # ✅ robots.txt здесь
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # ✅ нужно для allauth
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "backend.context_processors.site_domain",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# =======================
# БАЗА ДАННЫХ (ТОЛЬКО POSTGRESQL)
# =======================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# =======================
# АУТЕНТИФИКАЦИЯ
# =======================
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = []

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# =======================
# ЛОКАЛИЗАЦИЯ
# =======================
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# =======================
# СТАТИКА И МЕДИА
# =======================
STATIC_URL = "/static/"

# 👇 Добавлено: чтобы в DEBUG Django видел твои файлы в /static/
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# 👇 Теперь collectstatic будет складывать в отдельную папку
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =======================
# CORS + DRF
# =======================
CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 30,
}

# =======================
# JWT
# =======================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =======================
# Custom security
# =======================
SECURITY_ADMIN_SESSION_KEY = "admin_internal_allowed"

# =======================
# SITE DOMAIN
# =======================
SITE_ID = 1
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "http://127.0.0.1:8000")

# =======================
# SECURITY FLAGS
# =======================
if DEBUG:
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
else:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# =======================
# EMAIL (SMTP)
# =======================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@izotovlife.ru")

# =======================
# ALLAUTH (соц. логин)
# =======================
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_EMAIL_REQUIRED = True

REST_USE_JWT = True
TOKEN_MODEL = None

SOCIALACCOUNT_PROVIDERS = {
    "vk": {
        "APP": {
            "client_id": os.getenv("VK_CLIENT_ID"),
            "secret": os.getenv("VK_SECRET"),
            "key": "",
        }
    },
    "yandex": {
        "APP": {
            "client_id": os.getenv("YANDEX_CLIENT_ID"),
            "secret": os.getenv("YANDEX_SECRET"),
            "key": "",
        }
    },
    "google": {
        "APP": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "secret": os.getenv("GOOGLE_SECRET"),
            "key": "",
        }
    },
}
