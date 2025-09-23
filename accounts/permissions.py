# backend/accounts/permissions.py
# Назначение: Кастомные разрешения для ролей пользователей (редактор, админ).
# Путь: backend/accounts/permissions.py

from rest_framework.permissions import BasePermission


class IsEditor(BasePermission):
    """Доступ только для редакторов или админов."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_editor() or user.is_admin()))
