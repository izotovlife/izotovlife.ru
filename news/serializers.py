# Путь: backend/news/serializers.py
# Назначение: Сериализаторы для категорий, статей, импортированных новостей и общий сериализатор News.
# Исправления:
#   - ✅ Добавлены seo_url и category_display для фронта.
#   - ✅ Ссылки теперь формируются по /news/<category>/<slug>/ и /news/<source>/<slug>/.
#   - ✅ Ничего не удалено из текущего функционала.

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import Article, Category, ImportedNews, NewsSource

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Полная версия категории для вывода в списках с картинкой."""
    news_count = serializers.IntegerField(read_only=True)
    top_image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "news_count", "top_image"]

    def get_top_image(self, obj):
        # Сначала берём самую свежую ImportedNews с картинкой
        news = (
            ImportedNews.objects.filter(category=obj)
            .exclude(image__isnull=True).exclude(image="")
            .order_by("-published_at")
            .first()
        )
        if news and news.image:
            return news.image

        # Если нет — берём самую свежую Article с обложкой
        art = (
            Article.objects.filter(categories=obj)
            .exclude(cover_image__isnull=True).exclude(cover_image="")
            .order_by("-created_at")
            .first()
        )
        if art and art.cover_image:
            return art.cover_image.url if hasattr(art.cover_image, "url") else art.cover_image

        # Fallback: заглушка из media/defaults/
        return settings.MEDIA_URL + "defaults/default_category.png"


class CategoryMiniSerializer(serializers.ModelSerializer):
    """Мини-версия категории (например, для шапки)."""
    class Meta:
        model = Category
        fields = ["name", "slug"]


class ArticleSerializer(serializers.ModelSerializer):
    """Сериализатор авторских статей."""
    summary = serializers.SerializerMethodField()
    seo_url = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "title", "slug", "content", "summary",
            "created_at", "published_at", "cover_image", "cover_image_url",
            "type", "seo_url", "category_display",
        ]

    def get_summary(self, obj):
        return (obj.content[:200] + "...") if obj.content else ""

    def get_seo_url(self, obj):
        try:
            return obj.seo_path
        except Exception:
            cat = obj.categories.first()
            cat_slug = cat.slug if cat else "news"
            return f"/news/{cat_slug}/{obj.slug}/"

    def get_category_display(self, obj):
        cat = obj.categories.first()
        return cat.name if cat else "Новости"

    def get_cover_image_url(self, obj):
        if getattr(obj, "cover_image", None):
            return obj.cover_image.url if hasattr(obj.cover_image, "url") else obj.cover_image
        return settings.MEDIA_URL + "defaults/default_news.png"


class NewsSourceSerializer(serializers.ModelSerializer):
    """Источник новостей (РИА, ТАСС и т.п.)."""
    class Meta:
        model = NewsSource
        fields = ["id", "name", "slug", "logo"]


class ImportedNewsSerializer(serializers.ModelSerializer):
    """Сериализатор импортированных новостей (RSS)."""
    source = NewsSourceSerializer(read_only=True)
    seo_url = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    external_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ImportedNews
        fields = [
            "id", "title", "slug",
            "summary",
            "image", "image_url", "link", "external_url",
            "published_at", "category", "created_at",
            "feed_url", "type", "source",
            "seo_url", "category_display",
        ]

    def get_summary(self, obj):
        return obj.summary.strip() if obj.summary else ""

    def get_external_url(self, obj):
        return obj.link or obj.feed_url or None

    def get_seo_url(self, obj):
        try:
            return obj.seo_path
        except Exception:
            return f"/news/{obj.slug}/"

    def get_category_display(self, obj):
        if obj.category:
            return obj.category.name
        if getattr(obj, "source_fk", None):
            return obj.source_fk.name
        return "Новости"

    def get_image_url(self, obj):
        if getattr(obj, "image", None):
            return obj.image
        return settings.MEDIA_URL + "defaults/default_news.png"


class NewsSerializer(serializers.Serializer):
    """Полиморфный сериализатор для объединённой ленты."""
    def to_representation(self, instance):
        if isinstance(instance, Article):
            return ArticleSerializer(instance, context=self.context).data
        elif isinstance(instance, ImportedNews):
            return ImportedNewsSerializer(instance, context=self.context).data
        return super().to_representation(instance)
