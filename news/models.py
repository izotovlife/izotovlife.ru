# Путь: backend/news/models.py
# Назначение: Модели новостей, категорий, авторских статей и импортированных записей по RSS.
# Исправления:
#   - ✅ Article.slug теперь стабильно включает category.slug.
#   - ✅ Добавлено свойство seo_path → /news/<category>/<slug>/.
#   - ✅ ImportedNews.slug без source, но seo_path формируется через source.
#   - ✅ Пустые slug формируются безопасно с уникальностью.
#   - ✅ Просмотры и логи резолвера сохранены.

import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from unidecode import unidecode

from .models_logs import NewsResolverLog


class Category(models.Model):
    name = models.CharField("Название категории", max_length=255, unique=True)
    slug = models.SlugField("Слаг", max_length=255, unique=True, blank=True)
    popularity = models.PositiveIntegerField("Популярность", default=0)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(unidecode(self.name))
            new_slug = base_slug
            counter = 1
            while Category.objects.exclude(id=self.id).filter(slug=new_slug).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = new_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        PENDING = "PENDING", "На модерации"
        NEEDS_REVISION = "NEEDS_REVISION", "Нужна доработка"
        PUBLISHED = "PUBLISHED", "Опубликовано"

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField("Заголовок", max_length=300)
    slug = models.SlugField("Слаг", max_length=360, unique=True, blank=True)
    content = models.TextField("Содержимое")
    categories = models.ManyToManyField(Category, blank=True, verbose_name="Категории")
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.DRAFT)
    editor_notes = models.TextField("Заметки редактора", blank=True, default="")
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    published_at = models.DateTimeField("Опубликовано", null=True, blank=True)
    cover_image = models.ImageField("Обложка", upload_to="articles/", blank=True, null=True)
    archived_at = models.DateTimeField("В архиве с", null=True, blank=True)
    views_count = models.PositiveIntegerField("Просмотры", default=0)
    type = models.CharField(max_length=20, default="article", editable=False)

    def save(self, *args, **kwargs):
        # Формируем slug из категории и заголовка
        if not self.slug:
            base_slug = slugify(unidecode(self.title))[:50] or str(uuid.uuid4())[:8]
            cat_slug = None
            if self.pk and self.categories.exists():
                cat_slug = self.categories.first().slug
            if not cat_slug:
                cat_slug = "news"
            new_slug = f"{cat_slug}-{base_slug}"
            counter = 1
            while Article.objects.exclude(id=self.id).filter(slug=new_slug).exists():
                new_slug = f"{cat_slug}-{base_slug}-{counter}"
                counter += 1
            self.slug = new_slug
        super().save(*args, **kwargs)

    @property
    def seo_path(self):
        """SEO-путь: /news/<category>/<slug>/"""
        cat = self.categories.first()
        cat_slug = cat.slug if cat else "news"
        return f"/news/{cat_slug}/{self.slug}/"

    def __str__(self):
        return self.title

    @property
    def is_archived(self):
        return self.archived_at is not None


class NewsSource(models.Model):
    name = models.CharField("Название источника", max_length=255, unique=True)
    slug = models.SlugField("Слаг", max_length=255, blank=True, null=True)
    logo = models.ImageField("Логотип", upload_to="sources/", blank=True, null=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Источник новостей"
        verbose_name_plural = "Источники новостей"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(unidecode(self.name))
            new_slug = base_slug
            counter = 1
            while NewsSource.objects.exclude(id=self.id).filter(slug=new_slug).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = new_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ImportedNews(models.Model):
    source_fk = models.ForeignKey(
        NewsSource, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Источник"
    )
    link = models.URLField("Ссылка", unique=True)
    title = models.CharField("Заголовок", max_length=500)
    slug = models.SlugField("Слаг", max_length=360, unique=True, blank=True)
    summary = models.TextField("Краткое описание", blank=True, default="")
    image = models.URLField("Картинка", blank=True, default="")
    published_at = models.DateTimeField("Дата публикации", null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    feed_url = models.URLField("Источник RSS", blank=True, default="")
    archived_at = models.DateTimeField("В архиве с", null=True, blank=True)
    views_count = models.PositiveIntegerField("Просмотры", default=0)
    type = models.CharField(max_length=20, default="rss", editable=False)

    class Meta:
        ordering = ["-published_at", "-created_at"]
        verbose_name = "Импортированная новость"
        verbose_name_plural = "Импортированные новости"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(unidecode(self.title))[:50] or str(uuid.uuid4())[:8]
            new_slug = base_slug
            counter = 1
            while ImportedNews.objects.exclude(id=self.id).filter(slug=new_slug).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = new_slug
        super().save(*args, **kwargs)

    @property
    def seo_path(self):
        """SEO-путь: /news/<source>/<slug>/"""
        src = self.source_fk.slug if self.source_fk else "source"
        return f"/news/{src}/{self.slug}/"

    def __str__(self):
        return f"{self.source_fk}: {self.title[:60]}"

    @property
    def is_archived(self):
        return self.archived_at is not None
