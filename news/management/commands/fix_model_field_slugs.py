# Путь: backend/news/management/commands/fix_model_field_slugs.py
# Назначение: Точная правка: для указанной модели и указанного поля (например, seo_slug/alias/url/slug)
#   пересчитать slug из поля-названия (по умолчанию ищет name/title/label/caption/heading),
#   выполнить транслит RU→LAT, обеспечить уникальность (…-2, …-3).
# Запуск:
#   python manage.py fix_model_field_slugs --model app_label.ModelName --slug-field <поле_слага> --dry-run
#   python manage.py fix_model_field_slugs --model app_label.ModelName --slug-field <поле_слага> --apply
# Доп. опции:
#   --name-field <поле_названия>  # если название не name/title/label/caption/heading
#   --all                         # править все записи, а не только "техничные"
#
# Примечания:
#   - НИЧЕГО лишнего не трогаем, только одно поле в одной модели.
#   - Перед применением всегда рекомендую запустить --dry-run.
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from django.db import transaction
from django.db.models import Q
from news.slug_utils import slugify_ru, make_unique

NAME_FIELDS = ["name", "title", "label", "caption", "heading"]

def is_suspicious(val: str) -> bool:
    if not val:
        return False
    s = str(val)
    if s.lower().startswith("category") or s.lower() in ("category", "bez_category"):
        return True
    for ch in s:
        o = ord(ch)
        if (0x0400 <= o <= 0x04FF) or o in (0x0451, 0x0401):
            return True
    return False

class Command(BaseCommand):
    help = "Пересчитывает slug в произвольной модели/поле с транслитом и уникальностью."

    def add_arguments(self, parser):
        parser.add_argument("--model", required=True, help="app_label.ModelName (например: pages.category)")
        parser.add_argument("--slug-field", required=True, help="Имя slug-поля (например: slug, seo_slug, alias, url, path)")
        parser.add_argument("--name-field", default=None, help="Поле для названия (по умолчанию: name/title/label/caption/heading)")
        parser.add_argument("--dry-run", action="store_true", help="Показать план (без изменений)")
        parser.add_argument("--apply", action="store_true", help="Применить изменения")
        parser.add_argument("--all", dest="fix_all", action="store_true", help="Править все записи (не только 'техничные')")

    def handle(self, *args, **opts):
        model_label = opts["model"]
        slug_field = opts["slug_field"]
        name_field = opts["name_field"]
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

        field_names = {f.name for f in model._meta.get_fields() if hasattr(f, "attname")}
        if slug_field not in field_names:
            raise CommandError(f"В модели {model_label} нет поля '{slug_field}'")
        if not name_field:
            name_field = next((n for n in NAME_FIELDS if n in field_names), None)
        if not name_field:
            raise CommandError(f"В модели {model_label} нет стандартного поля названия. Укажи --name-field вручную.")

        qs = model.objects.all()
        if not fix_all:
            # фильтруем по python-предикату: вытащим только pk и нужные поля, проверим в питоне
            ids = []
            for obj in model.objects.only("pk", slug_field).iterator(chunk_size=1000):
                if is_suspicious(getattr(obj, slug_field, "")):
                    ids.append(obj.pk)
            qs = model.objects.filter(pk__in=ids)

        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS(f"В {model_label} нечего чинить."))
            return

        self.stdout.write(self.style.NOTICE(f"Модель: {model_label} | поле: {slug_field} | имя из: {name_field} | к правке: {count}"))

        taken = set(model.objects.values_list(slug_field, flat=True))
        plan = []
        mapping = {}  # pk -> new_slug

        def exists_other(s, pk):
            return (s in taken) or (s in mapping.values())

        # Формируем план
        for obj in qs.order_by("pk").only("pk", name_field, slug_field).iterator(chunk_size=500):
            old = getattr(obj, slug_field, "") or ""
            name_val = getattr(obj, name_field, "") or ""
            base = slugify_ru(name_val)
            new = make_unique(base, lambda s, _pk=obj.pk: exists_other(s, obj.pk))
            status = "OK" if old == new else "CHANGE"
            plan.append((obj.pk, name_val, old, new, status))
            if status == "CHANGE":
                mapping[obj.pk] = new

        # Покажем первые 50 строк плана
        for row in plan[:50]:
            self.stdout.write(f"{row[0]:>6} | {row[1]} -> {row[2]} => {row[3]} [{row[4]}]")
        if len(plan) > 50:
            self.stdout.write(f"... ещё {len(plan)-50} строк скрыто ...")

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY-RUN завершён. БД не изменена."))
            return

        # Применяем
        with transaction.atomic():
            changed = 0
            for pk, new_slug in mapping.items():
                obj = model.objects.get(pk=pk)
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
