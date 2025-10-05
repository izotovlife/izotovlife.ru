# Путь: backend/security/middleware.py
# Назначение: Шлюз в закрытую админку. Пропускает внутрь _internal_admin/ ТОЛЬКО при наличии сессионного флага,
#             установленного после активации одноразового токена (/admin/<token>/).
#             Сохраняет ваши «доверенные IP» и опциональный bypass для суперюзера.
# Важно:
#   • Настоящая админка должна быть подключена ТОЛЬКО по settings.ADMIN_INTERNAL_URL (по умолчанию "/_internal_admin/"):
#       path("_internal_admin/", admin.site.urls)
#   • Прямой путь "/admin/" должен быть перехвачен в security.urls заглушкой (404) и "дверью" для токена:
#       path("admin/", admin_block)               -> 404
#       path("admin/<str:token>/", admin_token_gate)  -> активация токена + redirect в _internal_admin
#   • Этот middleware НЕ блокирует "/admin/<token>/" — токен обрабатывает view.
#
# Доп. настройки в settings.py (все опциональны):
#   ADMIN_INTERNAL_URL = "/_internal_admin/"
#   SECURITY_ADMIN_SESSION_KEY = "ADMIN_SESSION_OK"
#   TRUSTED_ADMIN_IPS = ["127.0.0.", "10.0.", "192.168.1."]  # префиксы
#   ALLOW_SUPERUSER_BYPASS = False  # если True — суперюзер пройдет в бою и без токена (не рекомендуется)
#
# Поведение:
#   DEBUG=True  -> (по умолчанию) пропускаем всех в _internal_admin/ для локалки. Чтобы требовать токен и в DEBUG,
#                  просто закомментируйте соответствующую ветку ниже.
#   DEBUG=False -> требуем флаг в сессии ИЛИ (опционально) доверенный IP ИЛИ (опционально) суперюзер-bypass.

from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponseForbidden

DEFAULT_ADMIN_INTERNAL_URL = "/_internal_admin/"
DEFAULT_SESSION_KEY = "ADMIN_SESSION_OK"


class AdminInternalGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.internal_url = getattr(settings, "ADMIN_INTERNAL_URL", DEFAULT_ADMIN_INTERNAL_URL).rstrip("/")
        self.session_key = getattr(settings, "SECURITY_ADMIN_SESSION_KEY", DEFAULT_SESSION_KEY)
        self.trusted_prefixes = tuple(getattr(settings, "TRUSTED_ADMIN_IPS", []))
        self.allow_superuser_bypass = bool(getattr(settings, "ALLOW_SUPERUSER_BYPASS", False))

    def __call__(self, request):
        path = (request.path or "").rstrip("/")

        # 1) Жёсткая защита от случайного публикационного косяка:
        #    если по какой-то причине кто-то опять вывесил админку на "/admin/",
        #    возвращаем 404. Это не помешает "/admin/<token>/" — оно обрабатывается view до middleware.
        if path == "/admin":
            return HttpResponseNotFound("<h1>Not Found</h1>")

        # 2) Шлюзим ТОЛЬКО внутренний путь админки (/_internal_admin)
        if path.startswith(self.internal_url):
            # --- Режим разработки: хотите — оставляйте свободный вход, хотите — закройте как в бою ---
            if settings.DEBUG:
                # Чтобы требовать токен и в DEBUG, закомментируйте следующую строку:
                return self.get_response(request)

            # --- Прод: проверяем флаг, доверенные IP, опционально суперюзера ---
            has_flag = bool(request.session.get(self.session_key, False))

            remote_ip = request.META.get("REMOTE_ADDR", "") or ""
            from_trusted_ip = remote_ip.startswith(self.trusted_prefixes) if self.trusted_prefixes else False

            is_superuser = bool(getattr(request, "user", None) and request.user.is_authenticated and request.user.is_superuser)

            # Главный путь — флаг. Остальное — опции совместимости.
            if not (has_flag or from_trusted_ip or (self.allow_superuser_bypass and is_superuser)):
                # В бою лучше отдавать 404, чтобы не палить наличие админки
                return HttpResponseNotFound("<h1>Not Found</h1>")

        return self.get_response(request)
