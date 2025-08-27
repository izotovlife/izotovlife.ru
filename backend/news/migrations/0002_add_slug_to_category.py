from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("news", "0001_initial"),  # замени на актуальный номер последней миграции
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="slug",
            field=models.SlugField(unique=True, default="temp-slug"),
            preserve_default=False,
        ),
    ]
