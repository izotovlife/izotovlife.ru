# backend/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    photo = models.ImageField(upload_to="authors/photos/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Связь пользователя с категорией новостей."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    category = models.ForeignKey(
        "news.Category",
        on_delete=models.CASCADE,
        related_name="subscribers",
    )

    class Meta:
        unique_together = ("user", "category")

    def __str__(self) -> str:
        return f"{self.user} -> {self.category}"

