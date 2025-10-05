# Путь: backend/pages/migrations/0003_alter_staticpage_content_to_ckeditor5.py
# Назначение: Перевод StaticPage.content на CKEditor 5 поле.

from django.db import migrations
import django_ckeditor_5.fields


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0002_alter_staticpage_content"),
    ]

    operations = [
        migrations.AlterField(
            model_name="staticpage",
            name="content",
            field=django_ckeditor_5.fields.CKEditor5Field(
                verbose_name="Содержимое",
                config_name="default",
            ),
        ),
    ]
