# ===== ФАЙЛ: news/migrations/0002_add_is_moderated.py =====
# ПУТЬ: <твой_проект>\backend\news\migrations\0002_add_is_moderated.py
# НАЗНАЧЕНИЕ: Добавляет отсутствующее поле is_moderated к таблице news_news.
# ОПИСАНИЕ: После fake-initial таблица осталась без этого поля. Поле по умолчанию False и с индексом.

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='is_moderated',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
