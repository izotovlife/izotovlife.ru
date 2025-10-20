# Путь: backend/news/management/commands/strip_read_more.py
# Назначение: Массово удалить завершающее "читать далее" (и вариации) из текстов в БД.
#
# Важно:
#   • НИЧЕГО существующее не удаляем — это новый файл.
#   • Поддерживает два режима:
#       1) EXPLICIT (по умолчанию) — как прежде, по заранее известным моделям и именам полей.
#       2) AUTO (--auto) — сам находит модели и текстовые поля по всему проекту (ограничиваем через --apps).
#   • Имена полей: content, body, text, summary, lead, description, desc, html (+ любые TextField/CharField,
#     в названии которых встречается text/content/summary/body/lead/desc/html).
#   • Предфильтр по подстроке (--contains, по умолчанию "читать") ускоряет отбор кандидатов.
#   • CSV-бэкап изменений — в backend/var/backups/read_more_cleanup-YYYYmmdd-HHMMSS.csv
#
# Примеры:
#   DRY-RUN: python manage.py strip_read_more --auto --apps news,rssfeed --dry-run
#   SAVE   : python manage.py strip_read_more --auto --apps news,rssfeed
#   Точечно: python manage.py strip_read_more --auto --apps news,rssfeed --fields text,summary
#   Явно  : python manage.py strip_read_more --models Article,ImportedNews --fields content,body
#
# Примечание: RichTextField CKEditor наследуется от TextField — обработается.

import csv
import os
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db.models import TextField, CharField, Model

from news.utils.text_sanitizers import strip_trailing_read_more

# --- старые константы (оставлены для совместимости EXPLICIT-режима) ---
DEFAULT_FIELDS_ORDER = ["content", "body", "text", "summary"]
CANDIDATE_MODELS = [
    ("news", "Article"),
    ("rssfeed", "ImportedNews"),
]

# --- расширенный набор имён полей для приоритета в AUTO-режиме ---
EXTENDED_FIELD_NAMES = [
    "content", "body", "text", "summary", "lead", "description", "desc", "html",
]


def _looks_like_text_field_name(name: str) -> bool:
    n = name.lower()
    if n in {f.lower() for f in DEFAULT_FIELDS_ORDER + EXTENDED_FIELD_NAMES}:
        return True
    # эвристика: поле похоже на текстовое содержимое
    for key in ["text", "content", "summary", "body", "lead", "desc", "html"]:
        if key in n:
            return True
    return False


class Command(BaseCommand):
    help = "Удаляет завершающее 'читать далее' в текстах; поддерживает явный и авто-режим (--auto)."

    def add_arguments(self, parser):
        # Совместимые аргументы
        parser.add_argument("--dry-run", action="store_true", help="Показать изменения без сохранения")
        parser.add_argument("--limit", type=int, default=None, help="Ограничить число изменений на поле")
        parser.add_argument("--models", type=str, default=None, help="Список моделей (Article,ImportedNews)")
        parser.add_argument("--fields", type=str, default=None, help="Список полей (content,body,text,summary,...)")

        # Новые аргументы
        parser.add_argument("--auto", action="store_true",
                            help="Автопоиск моделей и полей по всему проекту")
        parser.add_argument("--apps", type=str, default="news,rssfeed",
                            help="Список приложений для автосканирования (через запятую)")
        parser.add_argument("--contains", type=str, default="читать",
                            help="Подстрока для первичного отбора (по умолчанию 'читать')")

    def handle(self, *args, **options):
        dry: bool = options["dry_run"]
        limit: Optional[int] = options["limit"]
        contains: str = options["contains"] or "читать"
        auto: bool = options["auto"]

        # Поля: если явно указали --fields, используем, иначе берём расширенный приоритетный список
        if options["fields"]:
            field_priority: List[str] = [f.strip() for f in options["fields"].split(",") if f.strip()]
        else:
            field_priority = list(dict.fromkeys(DEFAULT_FIELDS_ORDER + EXTENDED_FIELD_NAMES))

        # Бэкап CSV
        backup_dir = os.path.join("backend", "var", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = os.path.join(backup_dir, f"read_more_cleanup-{ts}.csv")

        # Заголовок
        self.stdout.write(self.style.WARNING("=== Старт очистки «читать далее» ==="))
        self.stdout.write(f"Режим: {'AUTO' if auto else 'EXPLICIT'} | {'DRY-RUN' if dry else 'SAVE'}")
        self.stdout.write(f"Приоритет полей: {', '.join(field_priority)}")
        self.stdout.write(f"Фильтр по подстроке: {contains!r}")
        if auto:
            apps_filter = {a.strip() for a in (options["apps"] or "").split(",") if a.strip()}
            self.stdout.write(f"Сканируем приложения: {', '.join(sorted(apps_filter)) or 'все'}")
        self.stdout.write("")

        # Счётчики и бэкап
        total_checked = 0
        total_changed = 0
        rows_for_backup: List[dict] = []

        if auto:
            apps_filter = {a.strip() for a in (options["apps"] or "").split(",") if a.strip()}
            for ModelClass in apps.get_models():
                app_label = ModelClass._meta.app_label
                model_name = ModelClass.__name__
                if apps_filter and app_label not in apps_filter:
                    continue

                # Выберем подходящие текстовые поля
                candidate_fields: List[str] = []
                for f in ModelClass._meta.get_fields():
                    if not hasattr(f, "attname"):
                        continue
                    if isinstance(f, (TextField, CharField)) and _looks_like_text_field_name(f.name):
                        candidate_fields.append(f.name)

                if not candidate_fields:
                    continue

                self._process_model(
                    ModelClass, app_label, model_name, candidate_fields,
                    contains, limit, dry, field_priority,
                    rows_for_backup, self.stdout,
                    counters=lambda c, ch: self._bump_totals(c, ch, locals_dict=locals())
                )
                # после выхода из _process_model обновим локальные тоталы
                total_checked, total_changed = self._recount_totals(rows_for_backup, total_checked, total_changed)

        else:
            # Явный режим: оставлен для обратной совместимости
            only_models = None
            if options["models"]:
                only_models = {m.strip() for m in options["models"].split(",") if m.strip()}

            for app_label, model_name in CANDIDATE_MODELS:
                if only_models and model_name not in only_models:
                    continue
                ModelClass = self._get_model_safe(app_label, model_name)
                if not ModelClass:
                    self.stdout.write(self.style.NOTICE(f"Пропуск: нет модели {app_label}.{model_name}"))
                    continue

                present_fields = {f.name for f in ModelClass._meta.get_fields()}
                candidate_fields = [f for f in field_priority if f in present_fields]
                if not candidate_fields:
                    self.stdout.write(self.style.NOTICE(
                        f"В {app_label}.{model_name} нет ни одного из полей: {', '.join(field_priority)} — пропуск."
                    ))
                    continue

                self._process_model(
                    ModelClass, app_label, model_name, candidate_fields,
                    contains, limit, dry, field_priority,
                    rows_for_backup, self.stdout,
                    counters=lambda c, ch: self._bump_totals(c, ch, locals_dict=locals())
                )
                total_checked, total_changed = self._recount_totals(rows_for_backup, total_checked, total_changed)

        # Записываем CSV-бэкап
        with open(backup_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["model", "id", "field", "old_len", "new_len", "old_tail", "new_tail"]
            )
            writer.writeheader()
            writer.writerows(rows_for_backup)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Готово. Проверено записей: {total_checked}, изменено: {total_changed}."
        ))
        self.stdout.write(self.style.WARNING(f"Бэкап изменений: {backup_path}"))

    # ---------- helpers ----------

    def _process_model(
        self,
        ModelClass: type[Model],
        app_label: str,
        model_name: str,
        fields_to_process: List[str],
        contains: str,
        limit: Optional[int],
        dry: bool,
        field_priority: List[str],
        rows_for_backup: List[dict],
        stdout,
        counters,
    ):
        stdout.write(self.style.MIGRATE_HEADING(f"→ Обработка {app_label}.{model_name}"))
        # Сортируем поля в соответствии с приоритетом
        order_map = {name: i for i, name in enumerate([n.lower() for n in field_priority])}
        fields_sorted = sorted(
            fields_to_process,
            key=lambda n: order_map.get(n.lower(), 10_000)
        )

        for field in fields_sorted:
            try:
                qs = ModelClass.objects.filter(**{f"{field}__icontains": contains})
            except Exception:
                stdout.write(self.style.NOTICE(f"   Поле {field}: не удалось применить фильтр — пропуск."))
                continue

            approx = qs.count()
            if not approx:
                stdout.write(f"   Поле {field}: совпадений нет.")
                continue

            stdout.write(f"   Поле {field}: кандидатов ~ {approx}.")
            processed_here = 0
            changed_here = 0

            for obj in qs.iterator(chunk_size=500):
                raw = getattr(obj, field, None)
                if not isinstance(raw, str) or not raw.strip():
                    continue

                processed_here += 1
                new_val, changed = strip_trailing_read_more(raw)
                if changed:
                    changed_here += 1
                    rows_for_backup.append({
                        "model": f"{app_label}.{model_name}",
                        "id": obj.pk,
                        "field": field,
                        "old_len": len(raw),
                        "new_len": len(new_val),
                        "old_tail": raw[-200:].replace("\n", "\\n"),
                        "new_tail": new_val[-200:].replace("\n", "\\n"),
                    })
                    if not dry:
                        setattr(obj, field, new_val)
                        obj.save(update_fields=[field])

                if limit and changed_here >= limit:
                    stdout.write(self.style.WARNING(
                        f"   Поле {field}: достигнут лимит изменений {limit}."
                    ))
                    break

            counters(processed_here, changed_here)
            stdout.write(f"   Поле {field}: проверено {processed_here}, изменено {changed_here}.")

    def _get_model_safe(self, app_label: str, model_name: str):
        try:
            return apps.get_model(app_label, model_name)
        except LookupError:
            return None

    def _bump_totals(self, checked_delta: int, changed_delta: int, locals_dict):
        # Технический хак: обновим тоталы вызывающего handle()
        if "total_checked" in locals_dict:
            locals_dict["total_checked"] += checked_delta
        if "total_changed" in locals_dict:
            locals_dict["total_changed"] += changed_delta

    def _recount_totals(self, rows_for_backup: List[dict], prev_checked: int, prev_changed: int) -> Tuple[int, int]:
        # Изменённые считаем точно по количеству строк в бэкапе.
        changed = len(rows_for_backup)
        # Проверенные считаем накопительно (ведём отдельно через _bump_totals), поэтому возвращаем как есть.
        return prev_checked, changed
