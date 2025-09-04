# Путь: backend/news/serializers.py
# Назначение: сериализаторы новостей и категорий. Безопасная сериализация
#             при отсутствующих связях (author/category), поддержка создания.

from rest_framework import serializers
from .models import News, Category


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категорий."""

    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class NewsSerializer(serializers.ModelSerializer):
    """
    Сериализатор чтения новостей.
    - category: вложенный объект или null
    - author: компактный словарь (id, username) или null
    """

    link = serializers.URLField(allow_null=True, required=False)
    image = serializers.URLField(allow_null=True, required=False)
    content = serializers.CharField(allow_null=True, required=False)
    category = CategorySerializer(read_only=True, allow_null=True)
    author = serializers.SerializerMethodField()

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

    def get_author(self, obj):
        user = getattr(obj, "author", None)
        if not user:
            return None
        return {
            "id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
        }


class NewsCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания новости автором."""

    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = News
        fields = ["title", "link", "image", "content", "category"]
