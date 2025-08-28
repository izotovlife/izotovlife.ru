from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0006_auto_20250826_2256"),
    ]

    operations = [
        migrations.AddField(
            model_name="news",
            name="views_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
