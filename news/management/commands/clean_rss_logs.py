# Путь: backend/news/management/commands/clean_rss_logs.py
# Назначение: удаляет старые логи импорта RSS (RSSImportLog) старше указанного количества дней.

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from news.models_logs import RSSImportLog


class Command(BaseCommand):
    help = "Очищает старые логи импорта RSS из таблицы RSSImportLog."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Удалить логи старше указанного количества дней (по умолчанию 30).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать, сколько записей будет удалено, не удаляя их реально.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry = options["dry_run"]
        threshold_date = timezone.now() - timedelta(days=days)

        old_logs = RSSImportLog.objects.filter(created_at__lt=threshold_date)
        count = old_logs.count()

        if dry:
            self.stdout.write(
                self.style.WARNING(f"Найдено {count} логов старше {days} дней (dry-run, без удаления).")
            )
        else:
            deleted, _ = old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Удалено {deleted} логов старше {days} дней.")
            )
