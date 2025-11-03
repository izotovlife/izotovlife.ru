# Путь: backend/news/serializers_favorites.py
# Назначение: DRF-сериализатор для отдачи избранного в "Кабинет читателя".

from rest_framework import serializers
from .models_favorites import Favorite


class FavoriteItemSerializer(serializers.ModelSerializer):
    # Клиенту удобнее иметь универсальные поля
    url = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = [
            "id",
            "slug",
            "title",
            "preview_image",
            "source_name",
            "published_at",
            "created_at",
            "url",
        ]

    def get_url(self, obj):
        # Ваш фронт открывает новости по /news/<slug>/
        if obj.slug:
            return f"/news/{obj.slug}/"
        return "/"
