# Путь: backend/security/admin.py
# Назначение: Регистрация AdminSessionToken в админке (только просмотр).

from django.contrib import admin
from .models import AdminSessionToken

@admin.register(AdminSessionToken)
class AdminSessionTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "used_at")
    search_fields = ("user__username", "token")
    readonly_fields = ("user", "token", "created_at", "used_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False




