# Путь: backend/news/management/commands/fix_model_slugs.py
# Назначение: Пересчитать slug у ЛЮБОЙ модели (укажем её ярлык app_label.ModelName),
# взяв название из name/title, с RU→LAT транслитом и обеспечением уникальности.
# По умолчанию правим только 'технические' записи (category-*, bez_category, кириллица).
#
# Пример запуска:
#   python manage.py fix_model_slugs --model pages.category --dry-run
#   python manage.py fix_model_slugs --model pages.category --apply
# Кастомные поля:
#   --name-field title    если поле названия называется не name, а иначе
#   --slug-field seo_slug если слаг хранится не в 'slug'
#   --all                 чинить все записи (не только подозрительные)

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db import transaction
from django.db.models import Q
from news.slug_utils import slugify_ru, make_unique

class Command(BaseCommand):
    help = "Пересчитывает slug у указанной модели (RU→LAT) с обеспечением уникальности."

    def add_arguments(self, parser):
        parser.add_argument("--model", required=True, help="app_label.ModelName, например: pages.category")
        parser.add_argument("--name-field", default=None, help="Поле с названием (по умолчанию name или title)")
        parser.add_argument("--slug-field", default="slug", help="Поле slug (по умолчанию slug)")
        parser.add_argument("--dry-run", action="store_true", help="Показать план (без изменений)")
        parser.add_argument("--apply", action="store_true", help="Применить изменения")
        parser.add_argument("--all", dest="fix_all", action="store_true", help="Чинить все записи (не только подозрительные)")

    def handle(self, *args, **opts):
        model_label = opts["model"]
        name_field = opts["name_field"]
        slug_field = opts["slug_field"]
        dry = opts["dry_run"]
        apply_changes = opts["apply"]
        fix_all = opts["fix_all"]

        if not dry and not apply_changes:
            raise CommandError("Укажи --dry-run или --apply")

        try:
            app_label, model_name = model_label.split(".", 1)
        except ValueError:
            raise CommandError("Формат --model app_label.ModelName (пример: pages.category)")

        model = apps.get_model(app_label, model_name)
        if model is None:
            raise CommandError(f"Модель {model_label} не найдена")

        fields = {f.name for f in model._meta.get_fields() if hasattr(f, "attname")}
        if slug_field not in fields:
            raise CommandError(f"В модели {model_label} нет поля '{slug_field}'")
        if not name_field:
            name_field = "name" if "name" in fields else ("title" if "title" in fields else None)
        if not name_field or name_field not in fields:
            raise CommandError(f"В модели {model_label} нет поля name/title (укажи --name-field)")

        qs = model.objects.all()
        if not fix_all:
            qs = qs.filter(
                Q(**{f"{slug_field}__startswith": "category"}) |
                Q(**{f"{slug_field}__iexact": "category"}) |
                Q(**{f"{slug_field}__iexact": "bez_category"}) |
                Q(**{f"{slug_field}__regex": r".*[А-Яа-яЁё].*"})
            )

        count = qs.count()
        label = f"{model._meta.app_label}.{model._meta.model_name}"
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"В {label} нечего чинить (подозрительных нет)."))
            return

        self.stdout.write(self.style.NOTICE(f"Модель: {label} | к правке: {count}"))
        taken = set(model.objects.values_list(slug_field, flat=True))
        plan = []
        mapping = {}

        def exists_other(s, pk):
            return (s in taken) or (s in mapping.values())

        for obj in qs.order_by("pk"):
            name_val = getattr(obj, name_field, "") or ""
            old = getattr(obj, slug_field, "") or ""
            base = slugify_ru(name_val)
            new = make_unique(base, lambda s, _pk=obj.pk: exists_other(s, obj.pk))
            status = "OK" if old == new else "CHANGE"
            plan.append((obj.pk, name_val, old, new, status))
            if status == "CHANGE":
                mapping[obj.pk] = new

        # Показать план (первые 50 строк)
        for row in plan[:50]:
            self.stdout.write(f"{row[0]:>6} | {row[1]} -> {row[2]} => {row[3]} [{row[4]}]")
        if len(plan) > 50:
            self.stdout.write(f"... ещё {len(plan)-50} строк скрыто ...")

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY-RUN завершён. БД не изменена."))
            return

        with transaction.atomic():
            changed = 0
            for pk, new_slug in mapping.items():
                obj = model.objects.get(pk=pk)
                # финальная проверка уникальности
                base = new_slug
                cand = base
                n = 2
                while model.objects.exclude(pk=pk).filter(**{slug_field: cand}).exists():
                    cand = f"{base}-{n}"
                    n += 1
                setattr(obj, slug_field, cand)
                obj.save(update_fields=[slug_field])
                changed += 1

        self.stdout.write(self.style.SUCCESS(f"Готово. Обновлено slug: {changed}"))
