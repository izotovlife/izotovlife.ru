# Путь: backend/news/management/commands/clean_incomplete_news.py
# Назначение: удаляет или очищает новости без текста и изображения.
# Особенности:
#   ✅ Проверяет Article и ImportedNews.
#   ✅ Логирует всё в RSSImportLog.
#   ✅ Опция --delete (по умолчанию удаляет).
#   ✅ Опция --limit=N (ограничение количества).

from django.core.management.base import BaseCommand
from news.models import Article, ImportedNews
from news.models_logs import RSSImportLog


class Command(BaseCommand):
    help = "Удаляет или очищает новости без текста и изображения."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Удалять записи вместо простого пропуска",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Проверить только указанное количество (например, --limit=500).",
        )

    def log(self, message, level="INFO"):
        RSSImportLog.objects.create(
            source_name="clean_incomplete_news",
            message=message,
            level=level,
        )

    def handle(self, *args, **options):
        limit = options.get("limit", 0)
        delete_mode = options.get("delete", True)
        total_deleted = 0

        for model in [Article, ImportedNews]:
            queryset = model.objects.all()
            if limit:
                queryset = queryset[:limit]

            to_delete = queryset.filter(
                cover_image__isnull=True,
                content__isnull=True,
            ) | queryset.filter(
                cover_image="",
                content="",
            )

            count = to_delete.count()
            if count == 0:
                self.stdout.write(self.style.NOTICE(f"{model.__name__}: всё в порядке."))
                continue

            if delete_mode:
                deleted, _ = to_delete.delete()
                self.stdout.write(self.style.ERROR(f"{model.__name__}: удалено {deleted} записей без текста/картинки."))
                self.log(f"{model.__name__}: удалено {deleted} неполных записей.", "WARNING")
                total_deleted += deleted
            else:
                self.stdout.write(self.style.WARNING(f"{model.__name__}: найдено {count} неполных, но не удалено."))
                self.log(f"{model.__name__}: найдено {count} неполных (без удаления).", "INFO")

        self.stdout.write(self.style.SUCCESS(f"✅ Готово! Всего удалено {total_deleted} неполных записей."))
        self.log(f"Готово! Всего удалено {total_deleted} неполных записей.", "INFO")
