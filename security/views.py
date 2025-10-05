# Путь: backend/security/views.py
# Назначение: Обычные Django-вьюхи (НЕ DRF). Логин суперпользователя и одноразовая «дверь».

import json
import secrets
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .models import AdminSessionToken

SESSION_FLAG = getattr(settings, "SECURITY_ADMIN_SESSION_KEY", "admin_internal_allowed")
ADMIN_INTERNAL_URL = getattr(settings, "ADMIN_INTERNAL_URL", "/_internal_admin/")

@csrf_exempt
@require_POST
def admin_session_login(request):
    """
    POST /api/security/admin-session-login/
      body JSON: {"username": "...", "password": "..."}
    Возвращает: {"ok": true, "redirect": "/admin/<token>/"}
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    if not username or not password:
        return HttpResponseBadRequest("username/password required")

    user = authenticate(request, username=username, password=password)
    if not user or not user.is_superuser:
        return HttpResponseBadRequest("Invalid credentials or not a superuser")

    # Авторизуем сессию
    login(request, user)

    # Создаём одноразовый токен
    token = secrets.token_urlsafe(48)
    AdminSessionToken.objects.create(user=user, token=token)

    # Возвращаем редирект на «дверь»
    return JsonResponse({"ok": True, "redirect": f"/admin/{token}/"})


def admin_token_gate(request, token: str):
    """
    GET /admin/<token>/
      - валидный, неиспользованный и не просроченный токен → ставим флаг в сессию и редиректим на /_internal_admin/
      - иначе → 404
    """
    try:
        t = AdminSessionToken.objects.select_related("user").get(token=token)
    except AdminSessionToken.DoesNotExist:
        return HttpResponseNotFound("<h1>Not Found</h1>")

    # Проверка неиспользованности и срока жизни (5 минут)
    if t.used_at is not None:
        return HttpResponseNotFound("<h1>Not Found</h1>")
    if timezone.now() > t.created_at + timezone.timedelta(minutes=5):
        return HttpResponseNotFound("<h1>Not Found</h1>")

    # Отмечаем токен использованным
    t.used_at = timezone.now()
    t.save(update_fields=["used_at"])

    # Ставим флаг доступа в сессию — именно тот, что в settings.SECURITY_ADMIN_SESSION_KEY
    request.session[SESSION_FLAG] = True

    # Внутренняя админка
    return HttpResponseRedirect(ADMIN_INTERNAL_URL)
