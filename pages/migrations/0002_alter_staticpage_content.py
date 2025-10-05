# Путь: backend/pages/migrations/0002_alter_staticpage_content.py
# Назначение: Историческая миграция без зависимости от ckeditor.fields (CKEditor 4).
# ИЗМЕНЕНО: удалён импорт ckeditor.fields; поле временно приводится к TextField.
#           Актуальная миграция 0003 уже переводит поле на CKEditor5Field.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="staticpage",
            name="content",
            field=models.TextField(verbose_name="Содержимое"),
        ),
    ]
