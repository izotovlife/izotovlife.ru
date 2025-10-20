# Путь: backend/settings.py
# Назначение: Основные настройки Django-проекта IzotovLife (News Aggregator, Django + React)
# Поддерживает: PostgreSQL через .env, DRF, JWT, CORS, соц.авторизацию, почту и защиту админки.
# ОБНОВЛЕНИЯ (ничего не удалено):
#   ✅ Добавлены константы проекта/фронтенда для регистрации и восстановления пароля:
#        PROJECT_NAME, FRONTEND_BASE_URL, FRONTEND_LOGIN_URL, FRONTEND_RESET_URL
#   ✅ Добавлен безопасный DEV-фоллбек почты: при DEBUG и пустом EMAIL_HOST_PASSWORD письма идут в консоль
#   ✅ Добавлен ACCOUNT_DEFAULT_HTTP_PROTOCOL для allauth
#   ✅ Добавлен EMAIL_SUBJECT_PREFIX (бренд в теме)
#   ✅ Опциональная поддержка прокси (SECURE_PROXY_SSL_HEADER) через USE_X_FORWARDED_PROTO
#   ✅ Ничего существующее не удалено — только дополнено
#   ✅ ДОБАВЛЕНО: корректный CORS при withCredentials (whitelist вместо allow_all)
#   ✅ ДОБАВЛЕНО: DEV_LAN_IP из .env для работы по локальной сети (например 192.168.0.58)
#   ✅ ДОБАВЛЕНО ДЛЯ РЕГИСТРАЦИИ/ВХОДА: allauth вход по логину ИЛИ email, привязка кастомного RegisterSerializer,
#      экспонирование заголовка Authorization для фронта, безопасные флаги SameSite для куки, добавлена SessionAuth в DRF.
#   ✅ ИСПРАВЛЕНО: SOCIALACCOUNT_PROVIDERS — теперь 'APP' задаётся ТОЛЬКО при наличии client_id и secret в .env,
#      иначе allauth берёт настройки из админки (SocialApp). Это устраняет ошибку client_id=None.
#   ✅ ДОБАВЛЕНО (важно для VK через ngrok): принудительный HTTPS для allauth, доверие к прокси, и whitelists для ngrok-домена.

from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse  # ✅ для разборки FRONTEND_BASE_URL
import os
from dotenv import load_dotenv

# =======================
# БАЗОВЫЕ ПУТИ И ЗАГРУЗКА .ENV
# =======================
BASE_DIR = Path(__file__).resolve().parent.parent

# Принудительная загрузка .env (гарантированно подхватывается)
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f".env загружен: {dotenv_path}")
else:
    print(f".env не найден по пути: {dotenv_path}")

# =======================
# КОНСТАНТЫ ПРОЕКТА / ФРОНТЕНДА (ДОБАВЛЕНО ДЛЯ РЕГИСТРАЦИИ/СБРОСА)
# =======================
PROJECT_NAME = os.getenv("PROJECT_NAME", "IzotovLife")

# База фронтенда: используется для построения ссылок в письмах и whitelists CORS/CSRF
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3001")

# Куда редиректить/ссылаться после успешной активации (используется в ActivateAccountView)
FRONTEND_LOGIN_URL = os.getenv("FRONTEND_LOGIN_URL", f"{FRONTEND_BASE_URL}/login")

# Базовый путь формы сброса пароля на фронте (используется в PasswordResetRequestView)
# Итоговая ссылка собирается как: {FRONTEND_RESET_URL}/{uid}/{token}/
FRONTEND_RESET_URL = os.getenv("FRONTEND_RESET_URL", f"{FRONTEND_BASE_URL}/reset-password")

# ✅ Новый удобный параметр: ваш LAN-IP фронта в dev (например "192.168.0.58")
DEV_LAN_IP = os.getenv("DEV_LAN_IP", "").strip()

# 🔒 NGROK/HTTPS (ДОБАВЛЕНО): публичный https-домен (для тестов через ngrok)
NGROK_HTTPS_DOMAIN = os.getenv(
    "NGROK_HTTPS_DOMAIN",
    "interimperial-untensile-joanie.ngrok-free.dev"  # ← можно переопределить в .env при смене туннеля
).strip()

# =======================
# БАЗОВЫЕ НАСТРОЙКИ
# =======================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

if DEBUG:
    ALLOWED_HOSTS = [
        "127.0.0.1",
        "localhost",
        "0.0.0.0",
        "testserver",
        # остался ваш старый IP, оставляем его, он не мешает
        "192.168.0.33",
    ]
    # ✅ добавим DEV_LAN_IP если задан
    if DEV_LAN_IP:
        ALLOWED_HOSTS.append(DEV_LAN_IP)
    # ✅ ДОБАВЛЕНО: разрешаем ngrok-домен
    if NGROK_HTTPS_DOMAIN:
        ALLOWED_HOSTS += [NGROK_HTTPS_DOMAIN, ".ngrok-free.dev"]
    # dedup
    ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))
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
    "django_extensions",

    # third-party
    "rest_framework",
    "corsheaders",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "rest_framework.authtoken",

    # соц-авторизация
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
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
    "image_guard",  # <-- ваше приложение-сторож
]

# =======================
# MIDDLEWARE
# =======================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # должно быть одним из первых
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "django.middleware.csrf.CsrfViewMiddleware",  # при чистом JWT можно оставить выключенным
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
                "django.template.context_processors.request",  # allauth требует это
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
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": POSTGRES_DB,
            "USER": POSTGRES_USER,
            "PASSWORD": POSTGRES_PASSWORD,
            "HOST": os.getenv("POSTGRES_HOST", "localhost"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
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
# CORS + CSRF (обновлено)
# =======================

# Оригинальные ваши строки — оставляю (ниже перезададим whitelist-ами)
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# 🔎 Экспонируем заголовок Authorization для фронта (удобно при отладке/аналитике)
CORS_EXPOSE_HEADERS = ["Content-Type", "Authorization"]  # ✅ ДОБАВЛЕНО

# Список доверенных источников для CSRF-токена (используется только в DEBUG)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://192.168.0.33",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
    "http://192.168.0.33:3003",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://192.168.0.33:3000",
    "http://localhost:3003",
    "http://127.0.0.1:3003",
]

# ✅ ПРАВИЛЬНЫЙ DEV-CORS/CSRF с credential'ами:
# django-cors-headers не любит пару (CORS_ALLOW_ALL_ORIGINS=True) + (CORS_ALLOW_CREDENTIALS=True).
# Поэтому в DEBUG сводим к whitelist.
if DEBUG:
    # разбор URL фронта
    parsed = urlparse(FRONTEND_BASE_URL)
    origin_from_front = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or (80 if parsed.scheme=='http' else 443)}"

    # явный whitelist CORS
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        origin_from_front,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
    ]
    # LAN-IP фронта (если задан)
    if DEV_LAN_IP:
        CORS_ALLOWED_ORIGINS += [
            f"http://{DEV_LAN_IP}:3000",
            f"http://{DEV_LAN_IP}:3001",
            f"http://{DEV_LAN_IP}:3002",
            f"http://{DEV_LAN_IP}:3003",
        ]
    # ✅ ДОБАВЛЕНО: разрешаем фронт/бек по ngrok (https)
    if NGROK_HTTPS_DOMAIN:
        CORS_ALLOWED_ORIGINS += [f"https://{NGROK_HTTPS_DOMAIN}"]

    # regex на любые локальные 3xxx
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^http://localhost:\d+$",
        r"^http://127\.0\.0\.1:\d+$",
    ] + ([rf"^http://{DEV_LAN_IP}:\d+$"] if DEV_LAN_IP else [])

    # объединённый CSRF-whitelist (переопределяет ваши два блока выше)
    CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(
        CORS_ALLOWED_ORIGINS + [
            origin_from_front,
            "http://localhost",
            "http://127.0.0.1",
        ]
    ))
    # ✅ ДОБАВЛЕНО: ngrok-домен в CSRF (https)
    if NGROK_HTTPS_DOMAIN and f"https://{NGROK_HTTPS_DOMAIN}" not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(f"https://{NGROK_HTTPS_DOMAIN}")

# =======================
# DRF
# =======================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 30,
}

# ⚙️ Для соц-логина через allauth удобно разрешить сессионную аутентификацию и для DRF-вью (не мешает JWT)
# (оставляем раньше заданный блок и ДОБАВЛЯЕМ явное включение SessionAuthentication)
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework_simplejwt.authentication.JWTAuthentication",
    "rest_framework.authentication.SessionAuthentication",  # ✅ ДОБАВЛЕНО
)

# троттлинг для API (исправлено)
REST_FRAMEWORK.setdefault("DEFAULT_THROTTLE_CLASSES", [
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
])
REST_FRAMEWORK.setdefault("DEFAULT_THROTTLE_RATES", {})

# базовые лимиты для всех API-запросов + отдельные для формы предложений
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].update({
    "anon": "1000/day",          # базовый лимит для неавторизованных пользователей
    "user": "5000/day",          # базовый лимит для авторизованных пользователей
    "suggest_burst": "5/min",    # короткий лимит для формы "Предложить новость"
    "suggest_sustained": "20/day",  # суточный лимит для формы "Предложить новость"
})

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
SECURITY_ADMIN_SESSION_KEY = "admin_internal_allowed"
SITE_ID = 1
SITE_DOMAIN = os.getenv("SITE_DOMAIN", "http://127.0.0.1:8000")
TRUSTED_ADMIN_IPS = [
    ip.strip()
    for ip in os.getenv("TRUSTED_ADMIN_IPS", "127.0.0.1,::1").split(",")
    if ip.strip()
]

# 💡 безопасные SameSite для кук (в т.ч. для allauth-попапа — не повредит)
SESSION_COOKIE_SAMESITE = "Lax"  # ✅ ДОБАВЛЕНО
CSRF_COOKIE_SAMESITE = "Lax"     # ✅ ДОБАВЛЕНО

if DEBUG:
    SECURE_SSL_REDIRECT = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SECURE = False
else:
    SECURE_SSL_REDIRECT = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# 🔒 NGROK/HTTPS (ДОБАВЛЕНО): всегда строим https-ссылки и доверяем заголовкам прокси
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"  # ⟵ важно для allauth при DEBUG+ngrok
USE_X_FORWARDED_HOST = True              # ⟵ чтобы Host брался из X-Forwarded-Host/ngrok
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Опционально учитываем обратный прокси, если выставляет заголовок X-Forwarded-Proto
if os.getenv("USE_X_FORWARDED_PROTO", "False").lower() in ("true", "1", "yes"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =======================
# EMAIL (исправлено и активировано)
# =======================
SUGGEST_NEWS_EMAIL_TO = os.getenv("SUGGEST_NEWS_EMAIL_TO", "izotovlife@yandex.ru")

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.yandex.ru")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 465))
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True").lower() in ("true", "1", "yes")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() in ("true", "1", "yes")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "izotovlife@yandex.ru")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)

# ✅ DEV-фоллбек: если DEBUG и нет пароля SMTP, шлём письма в консоль (для регистрации/сброса)
if DEBUG and not EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Бренд в теме писем
EMAIL_SUBJECT_PREFIX = os.getenv("EMAIL_SUBJECT_PREFIX", "[IzotovLife] ")

# =======================
# ALLAUTH
# =======================
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_EMAIL_REQUIRED = True
# Протокол для ссылок allauth
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https" if not DEBUG else "http"  # ← оставляем как было...
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"  # ...и принудительно переписываем на https для ngrok ✅

# ✅ Вход по логину ИЛИ e-mail (чтобы формы были дружелюбнее)
ACCOUNT_AUTHENTICATION_METHOD = "username_email"  # ✅ ДОБАВЛЕНО
ACCOUNT_USERNAME_REQUIRED = True                  # ✅ ДОБАВЛЕНО

REST_USE_JWT = True
TOKEN_MODEL = None

# --- ВАЖНО: провайдеры соц.логина. Не задаём 'APP', если env пуст — тогда allauth возьмёт SocialApp из админки.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_SECRET = os.getenv("GOOGLE_SECRET", "").strip()
YANDEX_CLIENT_ID = os.getenv("YANDEX_CLIENT_ID", "").strip()
YANDEX_SECRET = os.getenv("YANDEX_SECRET", "").strip()
VK_CLIENT_ID = os.getenv("VK_CLIENT_ID", "").strip()
VK_SECRET = os.getenv("VK_SECRET", "").strip()

SOCIALACCOUNT_PROVIDERS = {
    "google": {},
    "yandex": {},
    "vk": {
        # Можно временно убрать scope, если в VK не одобрен email:
   "SCOPE": [],
    },
}

if GOOGLE_CLIENT_ID and GOOGLE_SECRET:
    SOCIALACCOUNT_PROVIDERS["google"]["APP"] = {
        "client_id": GOOGLE_CLIENT_ID,
        "secret": GOOGLE_SECRET,
        "key": "",
    }

if YANDEX_CLIENT_ID and YANDEX_SECRET:
    SOCIALACCOUNT_PROVIDERS["yandex"]["APP"] = {
        "client_id": YANDEX_CLIENT_ID,
        "secret": YANDEX_SECRET,
        "key": "",
    }

if VK_CLIENT_ID and VK_SECRET:
    SOCIALACCOUNT_PROVIDERS["vk"]["APP"] = {
        "client_id": VK_CLIENT_ID,
        "secret": VK_SECRET,
        "key": "",
    }

# ✅ Dj-Rest-Auth: используем наш кастомный RegisterSerializer (вы уже его расширяли)
REST_AUTH_REGISTER_SERIALIZERS = {
    "REGISTER_SERIALIZER": "accounts.serializers.RegisterSerializer",  # ✅ ДОБАВЛЕНО
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

# === НАСТРОЙКИ ПРОКСИ КАРТИНОК (ДОБАВЛЕНО) ===
THUMB_CACHE_DIR = os.path.join(BASE_DIR, "media", "thumb_cache")
os.makedirs(THUMB_CACHE_DIR, exist_ok=True)

# Форматы, которые будем пытаться отдавать по умолчанию (по приоритету)
THUMB_DEFAULT_FORMATS = ("webp", "jpg")  # можно расширить ('avif','webp','jpg') если pillow+libavif собраны

# Качество (1–100) для потерьных форматов
THUMB_DEFAULT_QUALITY = 82

# Максимальный размер исходного файла для скачивания (в байтах), чтобы не убить сервер огромными файлами
THUMB_MAX_ORIGINAL_BYTES = 8 * 1024 * 1024  # 8 MB

# Таймауты для скачивания внешних картинок
THUMB_REQUEST_TIMEOUT = (6.0, 12.0)  # (connect, read), seconds

# Путь: backend/settings.py
# Назначение: Добавить консольные логи для сети импортёра (rssfeed.net) не ломая существующие LOGGING.

# --- [ДОБАВЛЕНО] Логирование для импортёра RSS (rssfeed.net) ---
import logging

DEFAULT_CONSOLE_HANDLER = {
    "class": "logging.StreamHandler",
    "level": "INFO",
    "formatter": "simple",
}

DEFAULT_FORMATTERS = {
    "simple": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
}

LOGGING = globals().get("LOGGING", {"version": 1, "disable_existing_loggers": False, "handlers": {}, "formatters": {}, "loggers": {}})

# Объединим форматтеры/обработчики (не затирая существующие)
LOGGING.setdefault("formatters", {}).update({k: v for k, v in DEFAULT_FORMATTERS.items() if k not in LOGGING["formatters"]})
LOGGING.setdefault("handlers", {})
if "console" not in LOGGING["handlers"]:
    LOGGING["handlers"]["console"] = DEFAULT_CONSOLE_HANDLER

# Точечные логгеры
LOGGING.setdefault("loggers", {}).update({
    # сетевой слой импортёра: увидите коды типа LOCAL_BLOCKED_10013, TIMEOUT_* и т.п.
    "rssfeed.net": {
        "handlers": ["console"],
        "level": "INFO",
        "propagate": False,
    },
    # сама команда импорта (если вы логируете под этим именем)
    "rssfeed": {
        "handlers": ["console"],
        "level": "INFO",
        "propagate": True,
    },
})
# Путь: backend/settings.py
# Назначение: Мягкий оверрайд протокола для allauth в ЛОКАЛЬНОЙ разработке без ngrok.
# НИЧЕГО НЕ УДАЛЯЕМ — просто добавляем финальное условие.
if DEBUG and not NGROK_HTTPS_DOMAIN:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"
