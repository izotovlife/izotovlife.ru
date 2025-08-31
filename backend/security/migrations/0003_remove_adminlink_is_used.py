# backend/security/migrations/0003_remove_adminlink_is_used.py
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("security", "0002_alter_adminlink_created_at"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="adminlink",
            name="is_used",
        ),
    ]
