# Путь: backend/news/management/commands/scan_any_slug_candidates.py
# Назначение: Просканировать ВСЕ модели, найти поля-похожие-на-slug (slug/seo_slug/alias/code/url/path/…),
# и показать записи с «техническими» значениями (startswith 'category', 'bez_category', либо кириллица в slug-поле).
# Как это помогает: вы увидите точный ярлык модели (app_label.model_name) и имена полей, где нужно чинить.

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db.models import Q, CharField
from django.db.models.fields import SlugField

NAME_FIELDS = ["name", "title", "label", "caption", "heading"]
SLUG_LIKE_FIELDS = [
    "slug", "seo_slug", "slug_ru", "slug_en", "alias", "code", "url", "path", "key",
]

class Command(BaseCommand):
    help = "Сканирует все модели и показывает, где встречаются 'category-*'/'bez_category' или кириллица в полях-похожих-на-slug."

    def handle(self, *args, **kwargs):
        total = 0
        for model in apps.get_models():
            # собираем строковые поля
            fields = {f.name: f for f in model._meta.get_fields() if hasattr(f, "attname")}
            char_fields = [name for name, f in fields.items() if isinstance(f, (CharField, SlugField))]
            if not char_fields:
                continue

            # имя поля "для показа названия"
            name_field = next((n for n in NAME_FIELDS if n in fields), None)

            # какие поля считаем "slug-подобными"
            slug_like = [n for n in char_fields if (n in SLUG_LIKE_FIELDS) or ("slug" in n.lower())]
            if not slug_like:
                continue

            # строим OR-фильтр по всем slug-подобным полям
            q = Q()
            for fn in slug_like:
                q |= Q(**{f"{fn}__startswith": "category"})
                q |= Q(**{f"{fn}__iexact": "category"})
                q |= Q(**{f"{fn}__iexact": "bez_category"})
                q |= Q(**{f"{fn}__regex": r".*[А-Яа-яЁё].*"})

            try:
                qs = model.objects.filter(q)
                cnt = qs.count()
            except Exception:
                continue

            if not cnt:
                continue

            total += cnt
            label = f"{model._meta.app_label}.{model._meta.model_name}"
            self.stdout.write(self.style.NOTICE(f"\nМодель: {label} (подозрительных: {cnt})"))
            # покажем первые 25 строк и какие поля засветились
            show_fields = ["pk"] + ([name_field] if name_field else []) + slug_like[:4]
            for row in qs.order_by("pk").values_list(*show_fields)[:25]:
                as_text = " | ".join(str(x) for x in row)
                self.stdout.write(as_text)
            if cnt > 25:
                self.stdout.write(f"... ещё {cnt-25} строк скрыто ...")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("\nПодозрительных значений не найдено."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nИтого подозрительных записей: {total}"))
