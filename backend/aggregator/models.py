"""Database models for the RSS/Atom aggregator."""

from django.db import models


class Source(models.Model):
    """RSS/Atom feed source."""

    FORMAT_CHOICES = [("rss", "RSS"), ("atom", "Atom")]

    title = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default="rss")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.title


class Item(models.Model):
    """Single entry fetched from a source."""

    source = models.ForeignKey(
        Source, on_delete=models.CASCADE, related_name="items", db_index=True
    )
    guid = models.CharField(max_length=255, blank=True)
    link = models.URLField(max_length=1000)
    title = models.CharField(max_length=500)
    summary = models.TextField(blank=True)
    author = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=200, blank=True)
    image_url = models.URLField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    content_hash = models.CharField(max_length=40, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "guid"],
                name="uniq_item_guid",
                condition=~models.Q(guid=""),
            ),
            models.UniqueConstraint(
                fields=["source", "link"], name="uniq_item_link"
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.title

