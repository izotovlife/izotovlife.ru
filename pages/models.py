# Путь: backend/pages/models.py
# Назначение: Модель статических страниц для админки (с поддержкой визуального редактора CKEditor 5).
# Изменения:
#   - УДАЛЕНО: использование RichTextField (из django-ckeditor 4).
#   - ДОБАВЛЕНО: CKEditor5Field (из django-ckeditor-5), config_name="default".

from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field  # CKEditor 5 поле


class StaticPage(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("Слаг", max_length=255, unique=True, blank=True)
    content = CKEditor5Field("Содержимое", config_name="default")  # ✅ CKEditor 5
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
