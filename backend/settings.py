from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f".env загружен: {dotenv_path}")
else:
    print(f".env не найден по пути: {dotenv_path}")

PROJECT_NAME = os.getenv("PROJECT_NAME", "IzotovLife")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
FRONTEND_LOGIN_URL = os.getenv("FRONTEND_LOGIN_URL", f"{FRONTEND_BASE_URL}/login")
FRONTEND_RESET_URL = os.getenv("FRONTEND_RESET_URL", f"{FRONTEND_BASE_URL}/reset-password")
DEV_LAN_IP = os.getenv("DEV_LAN_IP", "").strip()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

if DEBUG:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost", "0.0.0.0", "testserver", "192.168.0.33"]
    if DEV_LAN_IP:
        ALLOWED_HOSTS.append(DEV_LAN_IP)
    ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))
else:
    ALLOWED_HOSTS = ["izotovlife.ru", "www.izotovlife.ru"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "django_extensions",          # если нет пакета — убери эту строку или установи пакет

    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "django.contrib.sites",
    "django.contrib.sitemaps",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.vk",
    "allauth.socialaccount.providers.yandex",

    "dj_rest_auth",
    "dj_rest_auth.registration",

    "accounts",
    "news.apps.NewsConfig",
    "moderation",
    "security",
    "rssfeed",
    "pages",
    "ckeditor",
    "image_guard",  # твой сторож картинок; если его нет — убери из списка
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "security.middleware.AdminInternalGateMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "backend.urls"

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

def _db_from_url(dsn: str):
    u = urlparse(dsn)
    if u.scheme not in ("postgres", "postgresql"):
        raise ValueError("Only postgres:// or postgresql:// are supported")
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": (u.path or "/").lstrip("/"),
        "USER": u.username or "",
        "PASSWORD": u.password or "",
        "HOST": u.hostname or "127.0.0.1",
        "PORT": str(u.port or 5432),
    }

DATABASES = {}
if os.getenv("DATABASE_URL"):
    DATABASES["default"] = _db_from_url(os.getenv("DATABASE_URL"))
elif all(os.getenv(k) for k in ("DB_NAME", "DB_USER", "DB_PASSWORD")):
    DATABASES["default"] = {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": str(os.getenv("DB_PORT", "5432")),
    }
elif all(os.getenv(k) for k in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": str(os.getenv("POSTGRES_PORT", "5432")),
    }
else:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = []
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOW_CREDENTIALS = True
if DEBUG:
    parsed = urlparse(FRONTEND_BASE_URL)
    origin_from_front = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or (80 if parsed.scheme=='http' else 443)}"
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        origin_from_front,
        "http://localhost:3000", "http://127.0.0.1:3000",
        "http://localhost:3001", "http://127.0.0.1:3001",
        "http://localhost:3002", "http://127.0.0.1:3002",
        "http://localhost:3003", "http://127.0.0.1:3003",
    ]
    if DEV_LAN_IP:
        CORS_ALLOWED_ORIGINS += [f"http://{DEV_LAN_IP}:{p}" for p in (3000,3001,3002,3003)]
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
    ] + ([rf"^http://{DEV_LAN_IP}:\d+$"] if DEV_LAN_IP else [])
    CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CORS_ALLOWED_ORIGINS + ["http://localhost", "http://127.0.0.1", origin_from_front]))
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = ["https://izotovlife.ru", "https://www.izotovlife.ru"]
    CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS[:]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 30,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/day",
        "user": "5000/day",
        "suggest_burst": "5/min",
        "suggest_sustained": "20/day",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SECURITY_ADMIN_SESSION_KEY = "admin_internal_allowed"
SITE_ID = 1
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "http://127.0.0.1:8000")
TRUSTED_ADMIN_IPS = [ip.strip() for ip in os.getenv("TRUSTED_ADMIN_IPS", "127.0.0.1,::1").split(",") if ip.strip()]

if DEBUG:
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
else:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

if os.getenv("USE_X_FORWARDED_PROTO", "False").lower() in ("true", "1", "yes"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SUGGEST_NEWS_EMAIL_TO = os.getenv("SUGGEST_NEWS_EMAIL_TO", "izotovlife@yandex.ru")
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.yandex.ru")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True").lower() in ("true", "1", "yes")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "izotovlife@yandex.ru")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
if DEBUG and not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_SUBJECT_PREFIX = os.getenv("EMAIL_SUBJECT_PREFIX", "[IzotovLife] ")

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https" if not DEBUG else "http"

REST_USE_JWT = True
TOKEN_MODEL = None

SOCIALACCOUNT_PROVIDERS = {
    "vk": {"APP": {"client_id": os.getenv("VK_CLIENT_ID"), "secret": os.getenv("VK_SECRET"), "key": ""}},
    "yandex": {"APP": {"client_id": os.getenv("YANDEX_CLIENT_ID"), "secret": os.getenv("YANDEX_SECRET"), "key": ""}},
    "google": {"APP": {"client_id": os.getenv("GOOGLE_CLIENT_ID"), "secret": os.getenv("GOOGLE_SECRET"), "key": ""}},
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "simple"}},
    "loggers": {"news.api_extra_views": {"handlers": ["console"], "level": "INFO", "propagate": False}},
}

THUMB_CACHE_DIR = os.path.join(BASE_DIR, "media", "thumb_cache")
os.makedirs(THUMB_CACHE_DIR, exist_ok=True)
THUMB_DEFAULT_FORMATS = ("webp", "jpg")
THUMB_DEFAULT_QUALITY = 82
THUMB_MAX_ORIGINAL_BYTES = 8 * 1024 * 1024
THUMB_REQUEST_TIMEOUT = (6.0, 12.0)
