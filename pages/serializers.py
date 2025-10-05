# backend/pages/serializers.py
# Назначение: Сериализаторы для статических страниц (публичный и админский).

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import StaticPage


class StaticPagePublicSerializer(serializers.ModelSerializer):
    """
    Публичная версия: отдать только нужные поля + seo_url.
    Предполагается, что во вьюхе мы фильтруем is_published=True.
    """
    seo_url = serializers.SerializerMethodField()

    class Meta:
        model = StaticPage
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "created_at",
            "updated_at",
            "seo_url",
        ]
        read_only_fields = fields  # публичный сериализатор только для чтения

    def get_seo_url(self, obj):
        # если на фронте маршрут вида /page/<slug> — поменяйте на нужный
        return f"/page/{obj.slug}/"


class StaticPageAdminSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для форм админки/CRUD через API.
    Добавляем UniqueValidator на slug, чтобы ловить дубль на уровне API.
    """
    slug = serializers.CharField(
        max_length=255,
        validators=[UniqueValidator(queryset=StaticPage.objects.all())],
    )

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
        read_only_fields = ["id", "created_at", "updated_at"]
