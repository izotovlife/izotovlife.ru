# backend/news/models.py
# Назначение: Модели новостей, категорий, авторских статей и импортированных записей по RSS.
# Добавлено: автоматическая генерация slug латиницей для Category.
# Путь: backend/news/models.py

from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)

    def save(self, *args, **kwargs):
        # Если slug пустой — генерируем его латиницей
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Черновик'
        PENDING = 'PENDING', 'На модерации'
        NEEDS_REVISION = 'NEEDS_REVISION', 'Нужна доработка'
        PUBLISHED = 'PUBLISHED', 'Опубликовано'

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=360, unique=True)
    content = models.TextField()  # HTML из WYSIWYG
    categories = models.ManyToManyField(Category, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    editor_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)
    cover_image = models.URLField(blank=True, default="")
    # Архив
    archived_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def is_archived(self):
        return self.archived_at is not None


class ImportedNews(models.Model):
    source = models.CharField(max_length=255)
    link = models.URLField(unique=True)
    title = models.CharField(max_length=500)
    summary = models.TextField(blank=True, default="")
    image = models.URLField(blank=True, default="")
    published_at = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Новое поле: адрес ленты
    feed_url = models.URLField(blank=True, default="")
    # Архив
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return f"{self.source}: {self.title[:60]}"

    @property
    def is_archived(self):
        return self.archived_at is not None
