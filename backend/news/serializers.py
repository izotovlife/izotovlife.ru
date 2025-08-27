# backend/news/serializers.py
# backend/news/serializers.py
# Путь: backend/news/serializers.py
# Назначение: сериализаторы новостей и категорий.

from rest_framework import serializers
from .models import News, Category


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категорий."""

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class NewsSerializer(serializers.ModelSerializer):
    """Сериализатор чтения новостей (с вложенной категорией и автором)."""

    category = CategorySerializer(read_only=True)
    author = serializers.StringRelatedField()

    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "link",
            "image",
            "content",
            "category",
            "source_type",
            "author",
            "created_at",
            "is_moderated",
        ]


class NewsCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания новости автором."""

    class Meta:
        model = News
        fields = ["title", "link", "image", "content", "category"]
