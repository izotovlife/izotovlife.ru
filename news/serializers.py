# backend/news/serializers.py
# Назначение: Сериализаторы для категорий, статей, импортированных новостей и общий сериализатор News.
# Добавлено: блок автора в ArticleSerializer (id, username, photo, bio).
# Путь: backend/news/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Article, Category, ImportedNews

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    news_count = serializers.IntegerField(read_only=True)  # количество новостей в категории

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "news_count"]


class AuthorMiniSerializer(serializers.ModelSerializer):
    """Краткая информация об авторе для статьи."""
    class Meta:
        model = User
        fields = ["id", "username", "photo", "bio"]


class ArticleSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    is_archived = serializers.SerializerMethodField()
    source_url = serializers.SerializerMethodField()
    author = AuthorMiniSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "status",
            "editor_notes",
            "cover_image",
            "categories",
            "created_at",
            "published_at",
            "archived_at",
            "is_archived",
            "source_url",
            "author",
        ]

    def get_is_archived(self, obj):
        return obj.archived_at is not None

    def get_source_url(self, obj):
        return getattr(obj, "source_url", None)


class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ["title", "slug", "content", "cover_image", "status"]


class ImportedNewsSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    is_archived = serializers.SerializerMethodField()
    source_url = serializers.SerializerMethodField()

    class Meta:
        model = ImportedNews
        fields = [
            "id",
            "source",
            "link",
            "title",
            "summary",
            "image",
            "published_at",
            "category",
            "archived_at",
            "is_archived",
            "source_url",
        ]

    def get_is_archived(self, obj):
        return obj.archived_at is not None

    def get_source_url(self, obj):
        return obj.link  # RSS = читать в источнике


class NewsSerializer(serializers.Serializer):
    """
    Универсальный сериализатор для Article и ImportedNews.
    """

    def to_representation(self, obj):
        if isinstance(obj, Article):
            return ArticleSerializer(obj, context=self.context).data
        elif isinstance(obj, ImportedNews):
            return ImportedNewsSerializer(obj, context=self.context).data
        return super().to_representation(obj)
