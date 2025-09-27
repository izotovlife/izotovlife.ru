# backend/news/management/commands/purge_empty_news.py
# Назначение: Менеджмент-команда для удаления уже загруженных «пустых» новостей.
# Безопасно: есть --dry-run (по умолчанию), покажет сколько будет удалено.
# Примеры:
#   python manage.py purge_empty_news               # только посчитать (dry-run)
#   python manage.py purge_empty_news --delete      # реально удалить
# Путь: backend/news/management/commands/purge_empty_news.py

from django.core.management.base import BaseCommand
from django.db import transaction
from news.utils.content_filters import filter_nonempty, annotate_has_text
from news import models

CANDIDATE_MODELS = []
for name in ("Article", "ImportedNews"):
    if hasattr(models, name):
        CANDIDATE_MODELS.append(getattr(models, name))

class Command(BaseCommand):
    help = "Удалить новости без содержания (оставлены только заголовки)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Выполнить удаление (без этого ключа — только подсчёт)",
        )

    def handle(self, *args, **options):
        really_delete = options.get("delete", False)
        total = 0
        total_deleted = 0

        for Model in CANDIDATE_MODELS:
            qs_all = Model.objects.all()
            qs_annotated = annotate_has_text(qs_all)
            empty_qs = qs_annotated.filter(has_text=False)
            count = empty_qs.count()
            total += count
            self.stdout.write(self.style.WARNING(f"{Model.__name__}: найдено пустых — {count}"))

            if really_delete and count:
                with transaction.atomic():
                    deleted, _ = empty_qs.delete()
                    total_deleted += deleted
                self.stdout.write(self.style.SUCCESS(f"{Model.__name__}: удалено {deleted}"))

        if not really_delete:
            self.stdout.write(self.style.NOTICE("DRY-RUN: ничего не удалено. Запустите с --delete."))

        self.stdout.write(self.style.SUCCESS(f"ИТОГО: найдено {total}, удалено {total_deleted}"))
