# Путь: backend/news/management/commands/scan_slug_models.py
# Назначение: Просканировать ВСЕ модели проекта, у которых есть поля slug и name/title,
# и показать те, у кого slug выглядит «технически»: startswith 'category', 'bez_category' или с кириллицей.

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db.models import Q

class Command(BaseCommand):
    help = "Сканирует все модели с полями slug и name/title и показывает 'технические' слаги (category-*, bez_category, кириллица)."

    def handle(self, *args, **kwargs):
        total = 0
        for model in apps.get_models():
            # какие поля есть у модели
            field_names = {f.name for f in model._meta.get_fields() if hasattr(f, "attname")}
            if "slug" not in field_names:
                continue
            name_field = "name" if "name" in field_names else ("title" if "title" in field_names else None)
            if not name_field:
                continue

            try:
                qs = model.objects.filter(
                    Q(slug__startswith="category") |
                    Q(slug__iexact="category") |
                    Q(slug__iexact="bez_category") |
                    Q(slug__regex=r".*[А-Яа-яЁё].*")
                )
                cnt = qs.count()
            except Exception:
                # на всякий случай пропускаем модели, где такой фильтр не поддержан
                continue

            if cnt:
                total += cnt
                label = f"{model._meta.app_label}.{model._meta.model_name}"
                self.stdout.write(self.style.NOTICE(f"\nМодель: {label} (подозрительных: {cnt})"))
                for pk, title, slug in qs.order_by("pk").values_list("pk", name_field, "slug")[:25]:
                    self.stdout.write(f"{pk:>6} | {title} -> {slug}")
                if cnt > 25:
                    self.stdout.write(f"... ещё {cnt-25} строк скрыто ...")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("\nПодозрительных слуг не найдено."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nИтого подозрительных записей: {total}"))
