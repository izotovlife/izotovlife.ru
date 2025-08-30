# backend/backend/settings.py
# Назначение: базовые настройки Django-проекта IzotovLife
# Путь: backend/backend/settings.py
# Описание: безопасные настройки для DEV/PROD, CORS/CSRF, JWT, Postgres, статика/медиа

# backend/backend/settings.py
# Назначение: базовые настройки Django-проекта IzotovLife
# Путь: backend/backend/settings.py
# Описание: безопасные настройки для DEV/PROD, CORS/CSRF, JWT, Postgres, статика/медиа

import os
from pathlib import Path
from datetime import timedelta

try:
    # Не обязателен; если python-dotenv не установлен — просто пропустим
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()  # загрузит переменные из backend/.env (если есть)
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# === РЕЖИМЫ ===
# DEV по умолчанию; для прод: ENV=prod в окружении (например в .env.prod)
ENV = os.getenv("ENV", "dev").lower()
DEBUG = (os.getenv("DEBUG", "1") == "1") if ENV == "dev" else False

# === СЕКРЕТЫ И ХОСТЫ ===
# Для DEV оставляем дефолт, чтобы не падало; в PROD — задаём в окружении
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-change-me-DO-NOT-USE-IN-PRODUCTION",
)

# В DEV разрешаем localhost; в PROD читаем домены из окружения
if DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
else:
    # Пример: ALLOWED_HOSTS=izotovlife.ru,www.izotovlife.ru
    ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# === ПРИЛОЖЕНИЯ ===
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Сторонние
    "rest_framework",
    "corsheaders",

    # Наши
    "news",
    "accounts",
    "aggregator",
    "backend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# === БАЗА ДАННЫХ (PostgreSQL) ===
# В DEV можно оставить локальные значения, в PROD — переменные окружения
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "izotovlife"),
        "USER": os.getenv("POSTGRES_USER", "Izotoff"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "Jn4jnbeWllmhjds"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# === ПОЛЬЗОВАТЕЛЬСКАЯ МОДЕЛЬ ===
AUTH_USER_MODEL = "accounts.User"

# === СЕССИИ ===
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", "600"))  # 10 минут
SESSION_SAVE_EVERY_REQUEST = True

# === CORS/CSRF ===
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CSRF_TRUSTED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
else:
    # Пример: CORS_ALLOWED_ORIGINS=https://izotovlife.ru,https://www.izotovlife.ru
    _cors = [o for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o]
    if _cors:
        CORS_ALLOWED_ORIGINS = _cors
    # Пример: CSRF_TRUSTED_ORIGINS=https://izotovlife.ru,https://www.izotovlife.ru
    CSRF_TRUSTED_ORIGINS = [o for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o]

# === СТАТИКА И МЕДИА ===
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# === DRF + JWT ===
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_DAYS", "1"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# === БЕЗОПАСНОСТЬ ДЛЯ PROD ===
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Дополнительно по желанию:
    # SECURE_HSTS_SECONDS = 31536000
    # SECURE_HSTS_INCLUDE_SUBДОМAINS = True
    # SECURE_HSTS_PRELOAD = True
# backend/settings.py

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": BASE_DIR / "django_cache",  # создаст папку рядом с manage.py
    }
}
BACKEND_BASE_URL = "http://127.0.0.1:8000"
