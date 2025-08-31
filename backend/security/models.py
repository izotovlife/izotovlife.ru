# backend/security/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta


class AdminLink(models.Model):
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)  # ✅ поле в БД

    TTL_MINUTES = 5  # срок жизни ссылки (в минутах)

    def is_expired(self) -> bool:
        """
        Ссылка считается недействительной если:
        - уже использована (is_used == True)
        - прошло больше TTL минут с момента создания
        """
        if self.is_used:
            return True
        expiry_time = self.created_at + timedelta(minutes=self.TTL_MINUTES)
        return timezone.now() > expiry_time

    def __str__(self) -> str:
        return f"AdminLink(token={self.token}, used={self.is_used})"
