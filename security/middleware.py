# backend/security/middleware.py
# Назначение: Ограничение доступа в админку. В DEBUG пропускаем всех, в бою — только доверенные IP или суперюзеры.
# Путь: backend/security/middleware.py

from django.conf import settings
from django.http import HttpResponseForbidden


class AdminInternalGateMiddleware:
    """
    Если DEBUG=True → пропускаем всех (локальная разработка).
    Если DEBUG=False → пускаем в /admin/ только:
      - у кого в сессии стоит SECURITY_ADMIN_SESSION_KEY=True (например, после отдельной проверки),
      - или из доверённых IP (settings.TRUSTED_ADMIN_IPS),
      - или если пользователь суперюзер.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DEBUG:
            return self.get_response(request)

        path = request.path or ""
        if path.startswith("/admin/"):
            allowed = request.session.get(settings.SECURITY_ADMIN_SESSION_KEY, False)
            ip = request.META.get("REMOTE_ADDR", "")
            trusted = any(ip.startswith(prefix) for prefix in getattr(settings, "TRUSTED_ADMIN_IPS", []))

            if not (allowed or trusted or request.user.is_superuser):
                return HttpResponseForbidden("Доступ в админку запрещён")

        return self.get_response(request)
