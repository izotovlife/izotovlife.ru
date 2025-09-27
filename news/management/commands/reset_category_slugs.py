from django.core.management.base import BaseCommand
from news.models import Category
from django.utils.text import slugify
from unidecode import unidecode


class Command(BaseCommand):
    help = "Перегенерация slug для всех категорий (транслитерация)"

    def handle(self, *args, **kwargs):
        updated = 0
        for cat in Category.objects.all():
            new_slug = slugify(unidecode(cat.name))
            if not new_slug:
                new_slug = "category"
            base_slug = new_slug
            counter = 1
            while Category.objects.exclude(id=cat.id).filter(slug=new_slug).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1

            if cat.slug != new_slug:
                self.stdout.write(f"{cat.name}: {cat.slug} → {new_slug}")
                cat.slug = new_slug
                cat.save(update_fields=["slug"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Готово! Обновлено: {updated}"))
