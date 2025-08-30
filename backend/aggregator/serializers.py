"""Serializers for the aggregator API."""

from rest_framework import serializers

from .models import Source, Item


class SourceSerializer(serializers.ModelSerializer):
    """Serialize Source objects."""

    class Meta:
        model = Source
        fields = ["id", "title", "url", "is_active", "format", "created_at"]


class ItemSerializer(serializers.ModelSerializer):
    """Serialize Item objects with embedded source."""

    source = SourceSerializer(read_only=True)

    class Meta:
        model = Item
        fields = [
            "id",
            "source",
            "guid",
            "link",
            "title",
            "summary",
            "author",
            "category",
            "image_url",
            "published_at",
            "content_hash",
            "created_at",
        ]

