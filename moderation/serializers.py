# backend/moderation/serializers.py
# Назначение: Сериализаторы для модерации (редакторская панель).
# Путь: backend/moderation/serializers.py

from rest_framework import serializers
from news.models import Article

class ModerationArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id','title','slug','content','status','editor_notes','created_at','published_at']
