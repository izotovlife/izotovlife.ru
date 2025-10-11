# Путь: backend/news/management/commands/fix_category_slugs.py
# Назначение: Пересчитать slug у Category из name (транслит RU→LAT), обеспечить уникальность.
# Запуск:
#   python manage.py fix_category_slugs --dry-run
#   python manage.py fix_category_slugs --apply
#   python manage.py fix_category_slugs --apply --update-article-slugs   (опционально)
#
# Ничего существующее не удаляем. Обновляем только поля slug.
# Опция --update-article-slugs дополнительно меняет префикс в Article.slug,
# если он начинался со старого slug категории (например, 'politika-...').

from django.core.management.base import BaseCommand
from django.db import transaction
from news.models import Category, Article
from news.slug_utils import slugify_ru, make_unique

class Command(BaseCommand):
    help = "Пересчитать slug у Category из name (RU→LAT), обеспечить уникальность. Опционально обновить префиксы в Article.slug."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Только показать, что будет изменено.")
        parser.add_argument("--apply", action="store_true", help="Применить изменения к БД.")
        parser.add_argument("--update-article-slugs", action="store_true", help="Обновлять префикс в Article.slug, если он начинался со старого slug категории.")

    def handle(self, *args, **opts):
        dry = opts["dry_run"]
        apply_changes = opts["apply"]
        up_art = opts["update_article_slugs"]

        if not dry and not apply_changes:
            self.stdout.write(self.style.WARNING("Передайте --dry-run (предпросмотр) или --apply (применить)."))
            return

        cats = list(Category.objects.all().order_by("id"))
        taken = set(Category.objects.values_list("slug", flat=True))
        plan = []      # (id, name, old_slug, new_slug, status)
        mapping = {}   # old_slug -> new_slug

        def exists_other(slug, current_old):
            # «занят», если уже встречается в базе/плане и это не собственный прежний slug
            return (slug in taken or slug in mapping.values()) and slug != current_old

        # 1) Формируем план
        for c in cats:
            base = slugify_ru(c.name)
            target = make_unique(base, lambda s, cur=c.slug: exists_other(s, cur))
            if c.slug == target:
                status = "OK"
            else:
                status = "CHANGE"
                mapping[c.slug] = target
            plan.append((c.id, c.name, c.slug, target, status))

        # 2) Покажем план
        self.stdout.write(self.style.NOTICE("План изменения slug категорий:"))
        for row in plan:
            self.stdout.write(f"{row[0]:>4} | {row[1]} -> {row[2]} => {row[3]} [{row[4]}]")

        if dry:
            self.stdout.write(self.style.SUCCESS("DRY-RUN завершён. БД не изменялась."))
            return

        # 3) Применяем
        with transaction.atomic():
            # Категории
            for c in cats:
                new_slug = mapping.get(c.slug)
                if new_slug and new_slug != c.slug:
                    c.slug = new_slug
                    c.save(update_fields=["slug"])

            # Опционально: префиксы в Article.slug
            if up_art and mapping:
                self.stdout.write(self.style.NOTICE("Обновляем префиксы в Article.slug ..."))
                updated = 0
                for old_slug, new_slug in mapping.items():
                    # статьи уже прикреплены к категории с новым slug (через FK), меняем только текстовый префикс
                    arts = Article.objects.filter(category__slug=new_slug)
                    for a in arts:
                        if a.slug.startswith(old_slug + "-"):
                            tail = a.slug[len(old_slug):]  # '-xxx'
                            base = f"{new_slug}{tail}".lstrip("-")
                            candidate = base
                            n = 2
                            while Article.objects.exclude(pk=a.pk).filter(slug=candidate).exists():
                                candidate = f"{base}-{n}"
                                n += 1
                            a.slug = candidate
                            a.save(update_fields=["slug"])
                            updated += 1
                self.stdout.write(self.style.SUCCESS(f"Article.slug обновлено: {updated}"))

        self.stdout.write(self.style.SUCCESS("Готово: новые slug категорий применены."))
