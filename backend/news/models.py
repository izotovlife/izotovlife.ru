# ===== ФАЙЛ: backend/news/models.py =====
# НАЗНАЧЕНИЕ: Django-модели новостного агрегатора.
# ОПИСАНИЕ:
#   Эта версия синхронизирована с существующей схемой БД (PostgreSQL):
#     - content → db_column="description"
#     - image → db_column="image_url"
#     - created_at → db_column="pub_date"
#     - source_type → db_column="source"
#     - category_id мапится на Category
#     - author_id указывает на кастомную модель User, но в БД FK пока на auth_user.
#       Чтобы не ломать схему, ставим db_constraint=False.
#     - is_approved, is_popular, is_moderated — отражены как в БД.
#
#   В будущем можно сделать миграцию для чистки и перевода FK на accounts_user.

from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)

    def __str__(self) -> str:
        return self.name


class News(models.Model):
    SOURCE_CHOICES = [
        ("rss", "RSS"),
        ("author", "Author"),
    ]

    # базовые поля
    title = models.CharField(max_length=500)
    link = models.URLField(max_length=500, null=True, blank=True)
    image = models.URLField(blank=True, null=True, db_column="image_url")
    content = models.TextField(blank=True, null=True, db_column="description")
    created_at = models.DateTimeField(db_column="pub_date", auto_now_add=True)

    # категория (news_category)
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="category_id",
        related_name="news",
    )

    # источник (rss/author)
    source_type = models.CharField(
        max_length=200,
        choices=SOURCE_CHOICES,
        db_column="source",
    )

    # автор (FK отключён на уровне ORM)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="author_id",
        related_name="news_items",
        db_constraint=False,
    )

    # мета-поля
    views_count = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    is_moderated = models.BooleanField(default=False, db_index=True)

    def __str__(self) -> str:
        return self.title

    class Meta:
        db_table = "news_news"
