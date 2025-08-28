# ===== ФАЙЛ: backend/views_security.py =====
# ПУТЬ: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\backend\backend\views_security.py
# НАЗНАЧЕНИЕ: Скрытая/одноразовая ссылка входа в админку.
# ОПИСАНИЕ:
#  - admin_login: принимает логин и пароль суперпользователя, генерирует токен и выдаёт URL /admin/<token>/.
#  - use_admin_link: по токену логинит суперпользователя, токен гасит, редиректит во внутренний путь /_internal_admin/.
#  - admin_logout: ручка выхода.
# Хранилище токенов — кэш Django. TTL 10 минут. Сессия тоже 10 минут бездействия.

import secrets
import json

from django.http import JsonResponse, HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.core.cache import cache
from django.views.decorators.http import require_POST
from django.utils import timezone

TOKEN_TTL_SECONDS = 10 * 60  # 10 минут
CACHE_KEY_PREFIX = "admin_magic_token:"  # ключи вида admin_magic_token:<token> -> {"user_id": ..., "exp": ...}


def _make_token() -> str:
    return secrets.token_urlsafe(32)


def _cache_set_token(token: str, payload: dict):
    cache.set(f"{CACHE_KEY_PREFIX}{token}", payload, timeout=TOKEN_TTL_SECONDS)


def _cache_pop_token(token: str):
    key = f"{CACHE_KEY_PREFIX}{token}"
    data = cache.get(key)
    if data is not None:
        cache.delete(key)
    return data


@require_POST
def admin_login(request: HttpRequest):
    """
    Проверяем логин и пароль суперпользователя и отдаём одноразовую ссылку.
    Формат запроса: JSON {"username": "...", "password": "..."}
    Возврат: {"url": "/admin/<token>/", "expires_in": 600}
    """
    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        body = {}
    username = body.get("username")
    password = body.get("password")

    if not username or not password:
        return HttpResponseBadRequest("Username and password required.")

    user = authenticate(request, username=username, password=password)
    if not user or not user.is_superuser:
        return HttpResponseBadRequest("Invalid credentials or not superuser.")

    token = _make_token()
    _cache_set_token(token, {
        "user_id": user.id,
        "created": timezone.now().isoformat(),
    })
    url = f"/admin/{token}/"
    return JsonResponse({"url": url, "expires_in": TOKEN_TTL_SECONDS})


def use_admin_link(request: HttpRequest, token: str):
    """
    Потребление одноразовой ссылки:
      - забираем payload из кэша (если нет — 400),
      - логиним пользователя, выставляем сессию на 10 минут бездействия,
      - редиректим внутрь /_internal_admin/
    """
    data = _cache_pop_token(token)
    if not data:
        return HttpResponseBadRequest("Link expired or invalid.")

    User = get_user_model()
    try:
        user = User.objects.get(id=data["user_id"], is_superuser=True)
    except User.DoesNotExist:
        return HttpResponseBadRequest("User no longer exists or not superuser.")

    login(request, user)
    # 10 минут бездействия — и сессия умрёт
    request.session.set_expiry(TOKEN_TTL_SECONDS)

    # Заходим во внутреннюю админку
    return HttpResponseRedirect("/_internal_admin/")


@require_POST
def admin_logout(request: HttpRequest):
    logout(request)
    request.session.flush()
    return JsonResponse({"status": "ok"})
