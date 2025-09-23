# backend/news/permissions.py
# Назначение: Права доступа DRF для проверки роли редактора (группа editors) или суперпользователь.
# Путь: backend/news/permissions.py

from rest_framework.permissions import BasePermission


def user_is_editor(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.groups.filter(name="editors").exists()
    except Exception:
        return False


class IsEditorOrSuperuser(BasePermission):
    message = "Доступ только для редакторов или суперпользователей."

    def has_permission(self, request, view):
        return user_is_editor(request.user)
