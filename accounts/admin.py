# backend/accounts/admin.py
# Назначение: Регистрация кастомной модели User в админке.
# Путь: backend/accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DJUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DJUserAdmin):
    # добавляем role в блок "Роль"
    fieldsets = DJUserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("role",)}),
    )
    add_fieldsets = DJUserAdmin.add_fieldsets + (
        ("Дополнительно", {"fields": ("role",)}),
    )

    list_display = ("username", "email", "role", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)


