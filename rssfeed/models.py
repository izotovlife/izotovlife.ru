# backend/rssfeed/models.py
# Назначение: Модель источников RSS для админки и импорта новостей.
# Путь: backend/rssfeed/models.py

from django.db import models


class RssFeedSource(models.Model):
    name = models.CharField("Название источника", max_length=255)
    url = models.URLField("URL RSS-ленты", unique=True)
    created_at = models.DateTimeField("Добавлен", auto_now_add=True)

    class Meta:
        verbose_name = "Источник RSS"
        verbose_name_plural = "Источники RSS"

    def __str__(self):
        return self.name
