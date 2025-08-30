"""Initial migration for aggregator app."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Source",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("url", models.URLField(unique=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "format",
                    models.CharField(
                        choices=[("rss", "RSS"), ("atom", "Atom")],
                        default="rss",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("guid", models.CharField(max_length=255, blank=True)),
                ("link", models.URLField(max_length=1000)),
                ("title", models.CharField(max_length=500)),
                ("summary", models.TextField(blank=True)),
                ("author", models.CharField(max_length=200, blank=True)),
                ("category", models.CharField(max_length=200, blank=True)),
                ("image_url", models.URLField(blank=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("content_hash", models.CharField(db_index=True, max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="aggregator.source",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="item",
            constraint=models.UniqueConstraint(
                condition=~models.Q(guid=""),
                fields=("source", "guid"),
                name="uniq_item_guid",
            ),
        ),
        migrations.AddConstraint(
            model_name="item",
            constraint=models.UniqueConstraint(
                fields=("source", "link"), name="uniq_item_link"
            ),
        ),
    ]

