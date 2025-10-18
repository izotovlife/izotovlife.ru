# Путь: backend/news/management/commands/warm_category_covers.py
# Назначение: Прогрев кеша обложек категорий; по желанию — дамп JSON в STATIC_ROOT/categories/covers.json.
# Пример:
#   python manage.py warm_category_covers
#   python manage.py warm_category_covers --dump-static

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings

from news.models import Category
from news.api.category_covers import choose_best_cover_for_category, _static_fallback_for_slug

class Command(BaseCommand):
    help = "Прогревает кеш обложек категорий; опционально сохраняет JSON в STATIC_ROOT/categories/covers.json"

    def add_arguments(self, parser):
        parser.add_argument("--dump-static", action="store_true", help="Сохранить JSON в STATIC_ROOT/categories/covers.json")

    def handle(self, *args, **opts):
        data = {}
        self.stdout.write(self.style.NOTICE("→ Прогреваем обложки категорий"))
        for cat in Category.objects.all().only("slug"):
            key = f"category_cover:{cat.slug}"
            try:
                url = choose_best_cover_for_category(cat) or _static_fallback_for_slug(cat.slug) or ""
            except Exception:
                url = _static_fallback_for_slug(cat.slug) or ""
            cache.set(key, url, 60 * 60)  # 1 час
            data[cat.slug] = url
            self.stdout.write(f"  {cat.slug}: {'✓' if url else '—'}")

        if opts["dump_static"]:
            static_root = Path(getattr(settings, "STATIC_ROOT", "staticfiles"))
            out_dir = static_root / "categories"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "covers.json"
            out_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"JSON сохранён: {out_file}"))

        self.stdout.write(self.style.SUCCESS("Готово"))
