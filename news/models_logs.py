# backend/news/models_logs.py
# Назначение: модель для хранения логов резолвера slug, чтобы показывать их в админке.

from django.db import models

class NewsResolverLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20)
    slug = models.CharField(max_length=255)
    message = models.TextField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.level}] {self.slug} @ {self.created_at:%Y-%m-%d %H:%M}"
