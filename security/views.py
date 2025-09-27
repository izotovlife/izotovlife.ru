# backend/security/views.py
# Назначение: Вьюхи для защищённого входа в админку через одноразовый токен.
# Путь: backend/security/views.py

import secrets
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .models import AdminSessionToken


def admin_entrypoint(request, token):
    """
    GET /api/security/admin-entry/<token>/
    Используется для входа по одноразовому токену.
    Авторизует суперпользователя и редиректит в /admin/.
    """
    token_obj = get_object_or_404(AdminSessionToken, token=token)

    # Уже использован → на главную
    if token_obj.used_at:
        return redirect("/")

    # Истёк → удаляем и запрещаем доступ
    if token_obj.is_expired():
        token_obj.delete()
        return HttpResponseForbidden("Токен устарел")

    # Логиним суперпользователя (явно указываем backend!)
    user = token_obj.user
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    # Помечаем токен как использованный
    token_obj.used_at = timezone.now()
    token_obj.save(update_fields=["used_at"])

    # Отмечаем сессию, что можно в админку
    request.session[settings.SECURITY_ADMIN_SESSION_KEY] = True

    # ✅ В DEV редиректим на http://localhost:8000/admin/
    if settings.DEBUG:
        return redirect("http://localhost:8000/admin/")
    # ✅ В PROD — относительный путь
    return redirect("/admin/")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_session_login(request):
    """
    POST /api/security/admin-session-login/
    Для фронта: создаёт одноразовый токен и возвращает admin_url.
    Работает только для суперпользователей.
    """
    user = request.user
    if not user.is_superuser:
        return JsonResponse({"detail": "Нет прав"}, status=403)

    # Создаём одноразовый токен
    token = secrets.token_urlsafe(32)
    AdminSessionToken.objects.create(user=user, token=token)

    # ✅ DEBUG → полный URL (чтобы фронт открыл бэкенд)
    # ✅ PROD → домен из SITE_DOMAIN
    if settings.DEBUG:
        admin_url = f"http://localhost:8000/api/security/admin-entry/{token}/"
    else:
        base = settings.SITE_DOMAIN.rstrip("/")
        admin_url = f"{base}/api/security/admin-entry/{token}/"

    return JsonResponse({"admin_url": admin_url})
