# backend/news/serializers.py
# Назначение: Сериализаторы для категорий, статей, импортированных новостей и общий сериализатор News.
# Исправления:
#   - ✅ Добавлены seo_url и category_display для фронта.
#   - ✅ Ссылки формируются по /news/<category>/<slug>/ и /news/source/<source>/<slug>/.
#   - ✅ Стабильный тип ("type") для обоих сериализаторов.
#   - ✅ ImportedNewsSerializer.source берётся из source_fk.
#   - ✅ Безопасный абсолютный image-URL для ImportedNews.

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
            return news.image  # URLField/CharField — уже абсолютный/относительный URL

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

    class Meta:
        model = Article
        fields = [
            "id", "title", "slug", "content", "summary",
            "created_at", "published_at", "cover_image",
            "type", "seo_url", "category_display",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # стабильно возвращаем тип
        data["type"] = "article"
        return data

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


class NewsSourceSerializer(serializers.ModelSerializer):
    """Источник новостей (РИА, ТАСС и т.п.)."""
    class Meta:
        model = NewsSource
        fields = ["id", "name", "slug", "logo"]


class ImportedNewsSerializer(serializers.ModelSerializer):
    """Сериализатор импортированных новостей (RSS)."""
    # ВАЖНО: читаем источник из связи source_fk
    source = NewsSourceSerializer(source="source_fk", read_only=True)
    seo_url = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = ImportedNews
        fields = [
            "id", "title", "slug", "summary", "image", "link",
            "published_at", "category", "created_at", "feed_url",
            "type", "source", "seo_url", "category_display",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # стабильно возвращаем тип
        data["type"] = "rss"
        return data

    def get_image(self, obj):
        """
        Возвращает абсолютный URL картинки:
        • если это ImageField — через .url
        • если это строка/URLField — возвращаем как есть
        • если есть request — делаем build_absolute_uri
        """
        if not obj.image:
            return None
        request = self.context.get("request")

        # Абсолютные URL — оставляем как есть
        if isinstance(obj.image, str) and obj.image.startswith(("http://", "https://")):
            return obj.image

        # File/ImageField
        if hasattr(obj.image, "url"):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url

        # Строковый путь (например, "/media/news/img.jpg")
        if isinstance(obj.image, str):
            return request.build_absolute_uri(obj.image) if request else obj.image

        return None

    def get_seo_url(self, obj):
        try:
            return obj.seo_path
        except Exception:
            # корректный префикс "source/"
            src_slug = getattr(getattr(obj, "source_fk", None), "slug", None) or "source"
            return f"/news/source/{src_slug}/{obj.slug}/"

    def get_category_display(self, obj):
        if obj.category:
            return obj.category.name
        if obj.source_fk:
            return obj.source_fk.name
        return "Новости"


class NewsSerializer(serializers.Serializer):
    """Полиморфный сериализатор для объединённой ленты."""
    def to_representation(self, instance):
        if isinstance(instance, Article):
            return ArticleSerializer(instance, context=self.context).data
        elif isinstance(instance, ImportedNews):
            return ImportedNewsSerializer(instance, context=self.context).data
        return super().to_representation(instance)
