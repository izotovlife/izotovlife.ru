# backend/accounts/management/commands/create_demo_users.py
# Назначение: Утилита для быстрого создания ролей.
# Путь: backend/accounts/management/commands/create_demo_users.py

from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = "Создаёт тестовых пользователей: автор/редактор"

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='author').exists():
            User.objects.create_user('author', password='author123', role='AUTHOR')
        if not User.objects.filter(username='editor').exists():
            User.objects.create_user('editor', password='editor123', role='EDITOR')
        self.stdout.write(self.style.SUCCESS('Созданы: author/author123, editor/editor123'))
