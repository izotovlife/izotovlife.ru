# backend/security/admin.py
# Назначение: Просмотр одноразовых токенов.
# Путь: backend/security/admin.py

from django.contrib import admin
from .models import AdminSessionToken

@admin.register(AdminSessionToken)
class AdminSessionTokenAdmin(admin.ModelAdmin):
    list_display = ('token', 'user', 'used', 'created_at')
    list_filter = ('used_at',)  # ✅ теперь указываем поле, а не property
    readonly_fields = ('token', 'user', 'created_at', 'used_at')


