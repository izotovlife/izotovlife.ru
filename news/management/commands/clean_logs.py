# Путь: backend/news/management/commands/clean_logs.py
# Назначение: универсальная команда для очистки старых логов (RSSImportLog и NewsResolverLog).
# Позволяет задать количество дней хранения и сделать dry-run.

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from news.models_logs import RSSImportLog
from news.models_logs import NewsResolverLog


class Command(BaseCommand):
    help = "Удаляет старые логи импорта RSS и резолвера новостей старше указанного количества дней."

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

        total_deleted = 0
        total_found = 0

        # --- Функция очистки для каждого типа ---
        def clean_model(model, name):
            nonlocal total_deleted, total_found
            queryset = model.objects.filter(created_at__lt=threshold_date)
            count = queryset.count()
            total_found += count
            if dry:
                self.stdout.write(self.style.WARNING(f"[{name}] найдено {count} записей старше {days} дней."))
            else:
                deleted, _ = queryset.delete()
                total_deleted += deleted
                self.stdout.write(self.style.SUCCESS(f"[{name}] удалено {deleted} записей."))

        # --- Очистка обеих таблиц ---
        clean_model(RSSImportLog, "RSSImportLog")
        clean_model(NewsResolverLog, "NewsResolverLog")

        if dry:
            self.stdout.write(self.style.NOTICE(f"Итого найдено {total_found} записей (dry-run)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Очистка завершена. Удалено всего {total_deleted} записей."))
