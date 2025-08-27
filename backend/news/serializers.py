# backend/news/serializers.py
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
        fields = ["id", "title", "link", "image", "content", "category", "source_type", "author", "created_at", "is_moderated"]
