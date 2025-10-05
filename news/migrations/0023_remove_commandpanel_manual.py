# Путь: backend/news/migrations/0023_remove_commandpanel_manual.py
# Назначение: Удалить фантомную модель CommandPanel, созданную ранее по ошибке.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        # ВАЖНО: оставь здесь номер твоей последней миграции, которая создала CommandPanel
        # У тебя это было: '0022_commandpanel_alter_newsresolverlog_options_and_more'
        ('news', '0022_commandpanel_alter_newsresolverlog_options_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CommandPanel',
        ),
    ]

