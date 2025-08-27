# backend/backend/management/commands/open_admin.py
# Путь: backend/backend/management/commands/open_admin.py
# Назначение: management-команда, создающая одноразовую ссылку входа в админку.

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from backend.views_security import _make_token, _cache_set_token, TOKEN_TTL_SECONDS


class Command(BaseCommand):
    help = "Генерирует одноразовую ссылку для входа в админку"

    def add_arguments(self, parser):
        parser.add_argument("--username", help="Имя суперпользователя", default=None)

    def handle(self, *args, **options):
        User = get_user_model()
        username = options.get("username")
        if username:
            try:
                user = User.objects.get(username=username, is_superuser=True)
            except User.DoesNotExist:
                self.stderr.write("Суперпользователь не найден")
                return
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stderr.write("Создайте суперпользователя через createsuperuser")
                return

        token = _make_token()
        _cache_set_token(token, {"user_id": user.id, "created": timezone.now().isoformat()})
        url = f"/admin/{token}/"
        self.stdout.write(self.style.SUCCESS(f"Ссылка: {url} (действует {TOKEN_TTL_SECONDS} секунд)"))
