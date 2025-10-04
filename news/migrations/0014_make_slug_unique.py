from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0013_populate_importednews_slugs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importednews",
            name="slug",
            field=models.SlugField(
                max_length=360,
                unique=True,
                blank=False,
                verbose_name="Слаг",
            ),
        ),
    ]
