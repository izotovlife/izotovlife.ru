# backend/pages/models.py
# Назначение: Модель статических страниц для админки (с поддержкой визуального редактора CKEditor).

from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField   # ✅ подключаем CKEditor


class StaticPage(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("Слаг", max_length=255, unique=True, blank=True)
    content = RichTextField("Содержимое")   # ✅ теперь поле с визуальным редактором
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        verbose_name = "Статическая страница"
        verbose_name_plural = "Статические страницы"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
