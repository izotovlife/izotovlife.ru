from django.db import migrations
from django.utils.text import slugify
import uuid


def gen_slug(title, pk):
    """Генерирует slug на основе title + pk (уникально)."""
    base = slugify(title)[:50] or str(uuid.uuid4())[:8]
    return f"{base}-{pk}"


def populate_slugs(apps, schema_editor):
    ImportedNews = apps.get_model("news", "ImportedNews")
    for obj in ImportedNews.objects.all():
        if not obj.slug:
            obj.slug = gen_slug(obj.title, obj.pk)
            obj.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0012_importednews_slug"),
    ]

    operations = [
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
    ]

