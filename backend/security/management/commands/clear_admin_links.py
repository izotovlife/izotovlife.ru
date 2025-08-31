# backend/security/management/commands/clear_admin_links.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from security.models import AdminLink


class Command(BaseCommand):
    help = "Удаляет устаревшие и использованные одноразовые ссылки для входа в админку"

    def handle(self, *args, **options):
        now = timezone.now()

        # выбираем все просроченные или использованные ссылки
        expired_links = AdminLink.objects.filter(
            is_used=True
        ) | AdminLink.objects.filter(
            created_at__lt=now - timezone.timedelta(minutes=AdminLink.TTL_MINUTES)
        )

        count = expired_links.count()

        if count > 0:
            expired_links.delete()
            self.stdout.write(self.style.SUCCESS(f"✅ Удалено {count} старых ссылок"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Нет устаревших или использованных ссылок"))
