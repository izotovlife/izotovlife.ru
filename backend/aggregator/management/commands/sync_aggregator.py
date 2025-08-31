# backend/aggregator/management/commands/sync_aggregator.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from aggregator.models import Item
from news.models import News, Category


class Command(BaseCommand):
    help = "Синхронизировать все записи Item → News (автосоздание категорий, публикация новостей)"

    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0

        for item in Item.objects.all():
            category_name = item.category or "Без категории"
            category, _ = Category.objects.get_or_create(
                title=category_name,
                defaults={"slug": slugify(category_name)}
            )

            news, created = News.objects.get_or_create(
                title=item.title,
                defaults={
                    "content": item.summary or item.title,
                    "image": item.image_url,
                    "category": category,
                    "is_approved": True,   # сразу публикуем
                    "is_popular": False,
                    "author": None,        # можно потом связать с пользователем
                }
            )

            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Синхронизация завершена. Добавлено {created_count}, пропущено {skipped_count}."
            )
        )
