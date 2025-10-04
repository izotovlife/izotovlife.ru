# backend/pages/serializers.py
# Назначение: Сериализатор для API статических страниц.

from rest_framework import serializers
from .models import StaticPage


class StaticPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticPage
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "is_published",
            "created_at",
            "updated_at",
        ]
