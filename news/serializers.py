# backend/news/serializers.py
# Назначение: Сериализаторы для категорий, статей, импортированных новостей и общий сериализатор News.
# Улучшено:
#   - В ArticleSerializer summary теперь виртуальное поле (первые 200 символов content).
#   - В ImportedNewsSerializer добавлено поле source (NewsSourceSerializer) для вывода логотипа и имени источника.
#   - Добавлен CategoryMiniSerializer для мини-версии категории.
#   - Подробные комментарии для понимания структуры данных.

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Article, Category, ImportedNews, NewsSource

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    """Полная версия категории для вывода в статьях и админке."""
    news_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "news_count"]

class CategoryMiniSerializer(serializers.ModelSerializer):
    """Мини-версия категории (например, для шапки) — без ID и счётчиков."""
    class Meta:
        model = Category
        fields = ["name", "slug"]

class ArticleSerializer(serializers.ModelSerializer):
    """
    Сериализатор авторских статей.
    Поле summary создаётся динамически из content (первые 200 символов),
    что позволяет показывать краткий анонс.
    """
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            "id", "title", "slug", "content", "summary",
            "created_at", "published_at", "cover_image", "type",
        ]

    def get_summary(self, obj):
        # Если есть содержимое, берём первые 200 символов, иначе возвращаем пустую строку
        return (obj.content[:200] + "...") if obj.content else ""

class NewsSourceSerializer(serializers.ModelSerializer):
    """Сериализатор источника (РИА, ТАСС и т.п.)."""
    class Meta:
        model = NewsSource
        fields = ["id", "name", "slug", "logo"]

class ImportedNewsSerializer(serializers.ModelSerializer):
    """
    Сериализатор импортированных новостей (RSS).
    Добавлено поле source: сериализация связанного объекта NewsSource
    для отображения логотипа и названия источника на фронтенде.
    """
    source = NewsSourceSerializer(read_only=True)

    class Meta:
        model = ImportedNews
        fields = [
            "id", "title", "summary", "image", "link",
            "published_at", "category", "created_at", "feed_url",
            "type", "source",
        ]

class NewsSerializer(serializers.Serializer):
    """
    Полиморфный сериализатор для объединённой ленты.
    В зависимости от типа instance возвращает данные из соответствующего сериализатора.
    """
    def to_representation(self, instance):
        if isinstance(instance, Article):
            return ArticleSerializer(instance, context=self.context).data
        elif isinstance(instance, ImportedNews):
            return ImportedNewsSerializer(instance, context=self.context).data
        return super().to_representation(instance)
