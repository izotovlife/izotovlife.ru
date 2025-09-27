# backend/news/management/commands/reset_popularity.py
# Назначение: Сброс или затухание популярности категорий.
# Можно обнулить популярность или уменьшить её на коэффициент (например, 0.9).
# Путь: backend/news/management/commands/reset_popularity.py

from django.core.management.base import BaseCommand
from news.models import Category
from django.db.models import F

class Command(BaseCommand):
    help = "Сброс или затухание популярности категорий"

    def add_arguments(self, parser):
        parser.add_argument(
            "--mode",
            type=str,
            choices=["reset", "decay"],
            default="decay",
            help="Режим: reset (обнуление) или decay (затухание)",
        )
        parser.add_argument(
            "--factor",
            type=float,
            default=0.9,
            help="Коэффициент затухания (используется только в режиме decay, по умолчанию 0.9 = -10%)",
        )

    def handle(self, *args, **options):
        mode = options["mode"]
        factor = options["factor"]

        if mode == "reset":
            updated = Category.objects.update(popularity=0)
            self.stdout.write(self.style.SUCCESS(f"✅ Популярность сброшена у {updated} категорий"))
        else:
            for cat in Category.objects.all():
                old = cat.popularity
                new_value = int(old * factor)
                if new_value != old:
                    cat.popularity = new_value
                    cat.save(update_fields=["popularity"])
            self.stdout.write(self.style.SUCCESS(f"✅ Популярность уменьшена с коэффициентом {factor}"))
