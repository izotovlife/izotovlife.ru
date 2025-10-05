# Путь: backend/settings.py
# Назначение: Основные настройки Django-проекта News Aggregator (Django + React)
# Поддерживает: PostgreSQL через .env, DRF, JWT, CORS, соц.авторизацию, почту и логику защиты админки.

from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# =======================
# БАЗОВЫЕ НАСТРОЙКИ
# =======================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

if DEBUG:
    ALLOWED_HOSTS = [
        "127.0.0.1",
        "localhost",
        "192.168.0.33",  # ✅ локальный IP твоего React сервера
        "testserver",
    ]
else:
    ALLOWED_HOSTS = ["izotovlife.ru", "www.izotovlife.ru"]

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
    "rest_framework.authtoken",

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
    "django_ckeditor_5",
]

# =======================
# MIDDLEWARE
# =======================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ✅ ОБЯЗАТЕЛЬНО первым
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
        "DIRS": [BASE_DIR / "backend" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "backend.context_processors.site_domain",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# =======================
# БАЗА ДАННЫХ
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
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =======================
# CORS + CSRF (исправленный)
# =======================
# =======================
# CORS + CSRF (исправленный финально)
# =======================
CORS_ALLOW_ALL_ORIGINS = False  # безопаснее, чем True
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:3003",      # ✅ твой фронтенд порт
    "http://127.0.0.1:3003",
    "http://192.168.0.33:3000",   # ✅ твой локальный IP
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
    "http://192.168.0.33:3000",
]

CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "accept",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# =======================
# DRF
# =======================
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
# ПРОЧЕЕ
# =======================
SECURITY_ADMIN_SESSION_KEY = "admin_internal_allowed"  # ваш ключ — middleware его использует
SITE_ID = 1
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "http://127.0.0.1:8000")

if DEBUG:
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
else:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# =======================
# EMAIL
# =======================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@izotovlife.ru")

# =======================
# ALLAUTH
# =======================
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_EMAIL_REQUIRED = True

REST_USE_JWT = True
TOKEN_MODEL = None

SOCIALACCOUNT_PROVIDERS = {
    "vk": {"APP": {"client_id": os.getenv("VK_CLIENT_ID"), "secret": os.getenv("VK_SECRET"), "key": ""}},
    "yandex": {"APP": {"client_id": os.getenv("YANDEX_CLIENT_ID"), "secret": os.getenv("YANDEX_SECRET"), "key": ""}},
    "google": {"APP": {"client_id": os.getenv("GOOGLE_CLIENT_ID"), "secret": os.getenv("GOOGLE_SECRET"), "key": ""}},
}

# =======================
# ЛОГИРОВАНИЕ
# =======================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "news.api_extra_views": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
# --- System checks: silence legacy CKEditor 4 warning (until we migrate 'pages') ---
SILENCED_SYSTEM_CHECKS = [
    *globals().get("SILENCED_SYSTEM_CHECKS", []),
]
# ===========================
# CKEditor 5 config (для админских/страничных форм)
# ===========================
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "underline", "strikethrough", "|",
            "link", "blockQuote", "code", "|",
            "bulletedList", "numberedList", "outdent", "indent", "|",
            "insertTable", "undo", "redo",
        ],
        "table": {
            "contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"],
        },
        "language": "ru",
    }
}

# =======================
# ⚙️ Безопасность админки (одноразовый вход) — ДОБАВЛЕНО
# =======================
ADMIN_INTERNAL_URL = "/_internal_admin/"          # ✅ реальный путь admin.site.urls
TRUSTED_ADMIN_IPS = ["127.0.0.", "192.168.", "10."]  # ✅ префиксы белого списка (по желанию)
ALLOW_SUPERUSER_BYPASS = False                    # ✅ в проде лучше False, чтобы вход был только через токен
