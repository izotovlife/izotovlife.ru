# backend/news/management/commands/cleanup_empty_news.py
# Назначение: Очистка базы от пустых статей и импортированных новостей с неинформативным содержимым или битой картинкой.
# Обновления:
# - Статьи считаются пустыми, если content короче 50 символов.
# - Импортированные новости удаляются, если summary короче 50 символов или в summary присутствует фраза "без содержимого".
# - Новости без картинки (image) также удаляются.
# - Чтобы удалить записи, запускайте с ключом --delete. Без ключа – только отчёт.

import asyncio
import httpx
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.functions import Length
from news.models import Article, ImportedNews

class Command(BaseCommand):
    help = "Удаляет/отмечает пустые записи и новости с битыми картинками"

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true", help="Фактически удалить найденные записи")
        parser.add_argument("--limit", type=int, default=500, help="Сколько картинок проверять за один запуск")

    def handle(self, *args, **options):
        delete_mode = options["delete"]
        limit = options["limit"]

        # Статьи без содержимого (короткое content)
        art_qs = Article.objects.annotate(text_len=Length("content"))
        empty_articles = art_qs.filter(Q(content__isnull=True) | Q(content__exact="") | Q(text_len__lt=50))
        count_art = empty_articles.count()
        if count_art:
            if delete_mode:
                empty_articles.delete()
                self.stdout.write(self.style.ERROR(f"Удалено пустых статей: {count_art}"))
            else:
                self.stdout.write(self.style.WARNING(f"Найдено пустых статей: {count_art} (запустите с --delete)"))
        else:
            self.stdout.write(self.style.SUCCESS("Пустых статей не найдено"))

        # Импортированные новости с коротким summary
        imp_qs = ImportedNews.objects.annotate(sum_len=Length("summary"))
        empty_imported = imp_qs.filter(
            Q(summary__isnull=True) | Q(summary__exact="") |
            Q(sum_len__lt=50) | Q(summary__icontains="без содержимого")
        )
        count_imp = empty_imported.count()
        if count_imp:
            if delete_mode:
                empty_imported.delete()
                self.stdout.write(self.style.ERROR(f"Удалено импортированных новостей: {count_imp}"))
            else:
                self.stdout.write(self.style.WARNING(f"Найдено пустых импортированных новостей: {count_imp} (запустите с --delete)"))
        else:
            self.stdout.write(self.style.SUCCESS("Пустых импортированных новостей не найдено"))

        # Импортированные новости без картинки
        no_image = ImportedNews.objects.filter(Q(image__isnull=True) | Q(image__exact=""))
        count_no_image = no_image.count()
        if count_no_image:
            if delete_mode:
                no_image.delete()
                self.stdout.write(self.style.ERROR(f"Удалено новостей без картинки: {count_no_image}"))
            else:
                self.stdout.write(self.style.WARNING(f"Найдено новостей без картинки: {count_no_image} (запустите с --delete)"))
        else:
            self.stdout.write(self.style.SUCCESS("Новостей без картинки не найдено"))
