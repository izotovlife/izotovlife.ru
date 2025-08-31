# C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\izotovlife.ru\backend\security\views.py

import secrets
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.http import JsonResponse

from .models import AdminLink


def create_admin_link(request):
    """
    Генерация одноразовой ссылки для входа в админку (живет 5 минут).
    """
    token = secrets.token_urlsafe(32)
    link = AdminLink.objects.create(token=token)
    return JsonResponse({"url": f"/admin/{link.token}/"})


def use_admin_link(request, token: str):
    """
    Использование ссылки: если не истек TTL и не использована ранее.
    """
    link = get_object_or_404(AdminLink, token=token, is_used=False)

    # проверка срока действия
    if link.is_expired():
        return JsonResponse({"error": "Ссылка устарела или уже использована"}, status=400)

    # первый и единственный успешный вход
    link.is_used = True   # ✅ теперь ставим флаг
    link.used_at = timezone.now()
    link.save()

    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        return JsonResponse({"error": "Суперпользователь не найден"}, status=400)

    login(request, user)
    return redirect("/admin/")  # ✅ редирект в кастомную админку


def admin_logout(request):
    """
    Выход из админки.
    """
    logout(request)
    return redirect("/")


