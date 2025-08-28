# ===== ФАЙЛ: backend/news/serializers.py =====
# ПУТЬ: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\backend\news\serializers.py
# НАЗНАЧЕНИЕ: DRF-сериализаторы для работы с новостями и категориями.
# ОПИСАНИЕ: Содержит сериализаторы чтения и создания новостей, а также категорий.

from rest_framework import serializers
from .models import News, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class NewsSerializer(serializers.ModelSerializer):
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
    """Сериализатор для создания новостей автором"""

    class Meta:
        model = News
        fields = ["title", "link", "image", "content", "category"]

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["author"] = request.user
        validated_data["source_type"] = "author"
        return News.objects.create(**validated_data)
