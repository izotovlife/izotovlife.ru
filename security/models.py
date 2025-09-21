# backend/security/models.py
# Назначение: Модель одноразового токена для входа суперпользователя в админку.
# Путь: backend/security/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class AdminSessionToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=128, unique=True)  # токен строка
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        """Считаем токен недействительным через 5 минут после создания"""
        return timezone.now() > self.created_at + timedelta(minutes=5)

    @property
    def used(self):
        """Флаг: использован ли токен"""
        return self.used_at is not None

    def __str__(self):
        status = "использован" if self.used else "активен"
        return f"{self.user.username} [{self.token[:8]}...] {status}"
