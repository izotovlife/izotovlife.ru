# Путь: backend/news/management/commands/fix_all_category_slugs.py
# Назначение: Найти во ВСЕХ моделях с полями name/title + slug записи вида
#   slug ∈ {'category', 'bez_category'} или slug начинается с 'category-' или содержит кириллицу,
# и пересчитать slug из названия (RU→LAT) с обеспечением уникальности.
# Запуск:
#   python manage.py fix_all_category_slugs --dry-run
#   python manage.py fix_all_category_slugs --apply
#
# Ничего старое не удаляем. Обновляем только slug-строки.

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from django.db.models import Q
from news.slug_utils import slugify_ru, make_unique

CANDIDATE_MODEL_NAMES = {"category", "categories", "rubric", "section"}

class Command(BaseCommand):
    help = "Пересчитать 'технические' слаги (category-*) во всех моделях с name/title+slug -> человекочитаемые RU→LAT."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Только показать план (без изменений).")
        parser.add_argument("--apply", action="store_true", help="Применить изменения к БД.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        apply_changes = opts["apply"]
        if not dry and not apply_changes:
            self.stdout.write(self.style.WARNING("Передайте --dry-run или --apply"))
            return

        # Соберём подходящие модели
        models = []
        for model in apps.get_models():
            # Поля модели
            field_names = {f.name for f in model._meta.get_fields() if hasattr(f, "attname")}
            if "slug" not in field_names:
                continue
            # заголовок может называться name или title
            name_field = "name" if "name" in field_names else ("title" if "title" in field_names else None)
            if not name_field:
                continue
            # фильтруем по названию модели (вежливый приоритет), но не строго
            mn = model._meta.model_name.lower()
            if (mn in CANDIDATE_MODEL_NAMES) or True:
                models.append((model, name_field))

        total_changed = 0
        total_skipped = 0

        for model, name_field in models:
            # попробуем быстро оценить, есть ли «подозрительные» слуги в этой модели
            try:
                qs = model.objects.filter(
                    Q(slug__startswith="category") |
                    Q(slug__iexact="category") |
                    Q(slug__iexact="bez_category") |
                    Q(slug__regex=r".*[А-Яа-яЁё].*")  # кириллица в слаге
                )
                count = qs.count()
            except Exception:
                continue

            if count == 0:
                continue

            self.stdout.write(self.style.NOTICE(f"\nМодель: {model._meta.label} (подозрительных: {count})"))

            # План по этой модели
            taken = set(model.objects.values_list("slug", flat=True))
            plan = []
            mapping = {}  # pk -> (old_slug, new_slug)

            def exists_other(slug, pk):
                return (slug in taken or slug in [n for (_, n) in mapping.values()])

            for obj in qs.order_by("pk"):
                old = getattr(obj, "slug", "") or ""
                name_val = getattr(obj, name_field, "") or ""
                base = slugify_ru(name_val)
                new = make_unique(base, lambda s, _pk=obj.pk: exists_other(s, obj.pk))
                status = "OK" if old == new else "CHANGE"
                plan.append((obj.pk, name_val, old, new, status))
                if status == "CHANGE":
                    mapping[obj.pk] = (old, new)

            # Печать плана по модели
            for row in plan[:50]:
                self.stdout.write(f"{row[0]:>6} | {row[1]} -> {row[2]} => {row[3]} [{row[4]}]")
            if len(plan) > 50:
                self.stdout.write(f"... ещё {len(plan) - 50} строк скрыто ...")

            if dry:
                total_skipped += len(plan)
                continue

            # Применяем
            with transaction.atomic():
                changed = 0
                for pk, (old, new) in mapping.items():
                    obj = model.objects.get(pk=pk)
                    # ещё раз проверим уникальность (на случай гонки)
                    base = new
                    cand = base
                    n = 2
                    while model.objects.exclude(pk=pk).filter(slug=cand).exists():
                        cand = f"{base}-{n}"
                        n += 1
                    setattr(obj, "slug", cand)
                    obj.save(update_fields=["slug"])
                    changed += 1

            total_changed += changed
            self.stdout.write(self.style.SUCCESS(f"Обновлено в {model._meta.label}: {changed}"))

        if dry:
            self.stdout.write(self.style.SUCCESS("\nDRY-RUN завершён. БД не изменена."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nГотово. Всего обновлено slug: {total_changed}; просмотрено записей: {total_changed + total_skipped}."))
