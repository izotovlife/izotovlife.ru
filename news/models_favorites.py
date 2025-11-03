# Путь: backend/news/models_favorites.py
# Назначение: Модель "Favorite" — избранные публикации пользователя (generic для разных типов контента).

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Пользователь",
    )

    # Generic ссылка на любую модель новости (Article, ImportedNews и т.п.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name="Тип объекта")
    object_id = models.PositiveIntegerField(verbose_name="ID объекта")
    content_object = GenericForeignKey("content_type", "object_id")

    # Удобные дубли для быстрого рендера списка (не источник истины!)
    slug = models.SlugField(max_length=255, db_index=True, verbose_name="Слаг", blank=True)
    title = models.CharField(max_length=500, verbose_name="Заголовок", blank=True)
    preview_image = models.URLField(max_length=1000, verbose_name="Картинка превью", blank=True)
    source_name = models.CharField(max_length=255, verbose_name="Источник", blank=True)
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата публикации")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлено")

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        unique_together = (("user", "content_type", "object_id"),)

    def __str__(self):
        return f"{self.user} → {self.content_type}:{self.object_id} ({self.slug})"
