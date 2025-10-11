# Путь: backend/news/management/commands/deep_scan_slug_values.py
# Назначение: Глубокий сканер: пройтись по всем моделям и всем строковым полям,
#   найти техничные "слаги" (начинаются с 'category', равны 'category'/'bez_category', либо содержат кириллицу),
#   вывести точные app_label.ModelName и ИМЕНА ПОЛЕЙ, где это встречается, с примерами значений.
# Примечания:
#   - НИЧЕГО не меняет в БД — только печатает.
#   - Итеративный обход, чтобы не съесть память.
#   - Этого достаточно, чтобы понять, какую именно модель и поле чинить.

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db.models import CharField, TextField
from django.db import connections, DEFAULT_DB_ALIAS

def is_suspicious(val: str) -> bool:
    if not val:
        return False
    s = str(val)
    # техничные случаи
    if s.lower().startswith("category"):
        return True
    if s.lower() in ("category", "bez_category"):
        return True
    # кириллица в предполагаемом слаге — тоже подозрительно
    for ch in s:
        o = ord(ch)
        if (0x0400 <= o <= 0x04FF) or o in (0x0451, 0x0401):  # кириллица + Ё/ё
            return True
    return False

class Command(BaseCommand):
    help = "Глубокое сканирование всех моделей/строковых полей на 'техничные' slug-значения."

    def handle(self, *args, **kwargs):
        total_hits = 0
        for model in apps.get_models():
            fields = [f for f in model._meta.get_fields() if hasattr(f, "attname")]
            # берём только строковые поля
            str_fields = [f for f in fields if isinstance(getattr(f, "target_field", f), (CharField, TextField))]
            if not str_fields:
                continue

            # пробуем итеративно пройтись по объектам модели
            try:
                qs = model.objects.all().only(*[f.name for f in str_fields]).iterator(chunk_size=500)
            except Exception:
                continue

            model_hits = []
            for obj in qs:
                row = {}
                for f in str_fields:
                    try:
                        v = getattr(obj, f.name, None)
                    except Exception:
                        v = None
                    if isinstance(v, str) and is_suspicious(v):
                        row[f.name] = v
                if row:
                    model_hits.append((obj.pk, row))

            if model_hits:
                total_hits += len(model_hits)
                label = f"{model._meta.app_label}.{model._meta.model_name}"
                self.stdout.write(self.style.NOTICE(f"\nМодель: {label} — найдено {len(model_hits)} записей"))
                # покажем до 30 примеров
                limit = 30
                for pk, mapping in model_hits[:limit]:
                    # соберём первые 4 поля, чтобы не распухало
                    items = list(mapping.items())[:4]
                    kv = " | ".join(f"{k}={v}" for k, v in items)
                    self.stdout.write(f"{pk:>6} | {kv}")
                if len(model_hits) > limit:
                    self.stdout.write(f"... ещё {len(model_hits)-limit} строк скрыто ...")

        if total_hits == 0:
            self.stdout.write(self.style.SUCCESS("\nГотово: подозрительных значений НЕ найдено."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nИТОГО подозрительных записей: {total_hits}"))
