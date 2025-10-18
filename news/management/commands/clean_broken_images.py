# Путь: backend/news/management/commands/clean_broken_images.py
# Назначение: Команда Django для очистки битых изображений у Article и ImportedNews.
# Что делает:
#   - Обходит свежие новости (по умолчанию 30 дней, можно расширить аргументом --days).
#   - Проверяет поля image / thumbnail / preview (если существуют).
#   - Если URL «битый», очищает поле (ставит пустую строку) и сохраняет.
#   - Ничего не удаляет. Логи пишет в консоль.
#
# Примеры:
#   python manage.py clean_broken_images
#   python manage.py clean_broken_images --days 120
#   python manage.py clean_broken_images --all
#
# После запуска фронтенд начнёт показывать такие новости в блоке текстовых.

from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from news.utils.image_check import is_image_url_alive

# Подгоните импорт моделей под ваш проект (ниже — самые распространённые имена)
from news.models import Article, ImportedNews  # noqa: F401


IMAGE_FIELD_CANDIDATES = ("image", "thumbnail", "preview", "image_url", "thumb")


def _iter_image_fields(obj):
    for name in IMAGE_FIELD_CANDIDATES:
        if hasattr(obj, name):
            yield name


def _get_url(obj, field_name):
    val = getattr(obj, field_name)
    # Поддержка как строковых полей, так и Django ImageField/FileField
    if not val:
        return ""
    return getattr(val, "url", val) or ""


class Command(BaseCommand):
    help = "Очищает битые картинки у Article и ImportedNews (без удаления новостей)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Глубина в днях (по умолчанию 30)")
        parser.add_argument("--all", action="store_true", help="Обрабатывать все записи, игнорируя --days")
        parser.add_argument("--dry-run", action="store_true", help="Только показать, что будет изменено")

    def handle(self, *args, **opts):
        days = opts["days"]
        do_all = opts["all"]
        dry = opts["dry_run"]

        since = timezone.now() - timedelta(days=days)
        self.stdout.write(self.style.NOTICE(f"==> clean_broken_images started (days={days}, all={do_all}, dry={dry})"))

        total_checked = total_cleaned = 0

        for model in (Article, ImportedNews):
            if do_all:
                qs = model.objects.all()
            else:
                # Пытаемся уважить разные поля дат
                if hasattr(model, "published_at"):
                    qs = model.objects.filter(published_at__gte=since)
                elif hasattr(model, "created_at"):
                    qs = model.objects.filter(created_at__gte=since)
                else:
                    qs = model.objects.all()

            self.stdout.write(self.style.WARNING(f"— Модель {model.__name__}: проверяем {qs.count()} записей"))

            with transaction.atomic():
                for obj in qs.iterator():
                    changed = False
                    for field in _iter_image_fields(obj):
                        url = _get_url(obj, field)
                        if not url:
                            continue
                        total_checked += 1
                        if not is_image_url_alive(url):
                            self.stdout.write(f"[{model.__name__} #{obj.pk}] поле '{field}' битое → очищаем")
                            # Пишем пустую строку (для FileField допустимо присвоить "" — это эквивалентно None)
                            setattr(obj, field, "")
                            changed = True
                    if changed:
                        total_cleaned += 1
                        if not dry:
                            obj.save(update_fields=[f for f in _iter_image_fields(obj)])

        self.stdout.write(self.style.SUCCESS(f"Готово: проверено ссылок: {total_checked}, очищено записей: {total_cleaned}"))
