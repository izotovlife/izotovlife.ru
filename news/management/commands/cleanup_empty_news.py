# backend/news/management/commands/cleanup_empty_news.py
# Назначение: Очистка базы от пустых статей/новостей и записей с битыми картинками.
# Улучшено:
#   - Пустые = content <50 символов (Article) и summary <50 символов (ImportedNews) + фраза "без содержим".
#   - Асинхронная проверка изображений с httpx, 20 параллельных запросов, таймауты 2 секунды.
#   - Параметр --limit управляет числом проверяемых картинок за проход (по умолчанию 500).
#   - --delete позволяет удалять найденные записи; без флага команда только сообщает, что нашла.

import asyncio
import httpx
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models.functions import Length
from news.models import Article, ImportedNews

async def _check_image(url: str, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> bool:
    """
    Проверяет изображение: возвращает True, если URL ведёт на действительное изображение (200 OK и content-type image/*),
    либо если изображение — стандартная заглушка default_news.png.
    """
    if not url:
        return False
    low = url.strip().lower()
    # Заглушку считаем валидной
    if low.endswith("default_news.png"):
        return True
    async with sem:
        try:
            r = await client.head(url, follow_redirects=True)
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ct.startswith("image/"):
                return True
            r = await client.get(url, follow_redirects=True)
            ct = r.headers.get("content-type", "")
            return r.status_code == 200 and ct.startswith("image/")
        except Exception:
            return False

async def _check_urls(urls: list[str]) -> list[bool]:
    """Возвращает список флагов is_ok (True/False) для каждой картинки."""
    timeout = httpx.Timeout(connect=2.0, read=2.0, write=2.0, pool=2.0)
    sem = asyncio.Semaphore(20)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [_check_image(u, client, sem) for u in urls]
        return await asyncio.gather(*tasks)

class Command(BaseCommand):
    help = (
        "Удаляет/отмечает пустые записи и новости с битыми картинками.\n"
        "Пустыми считаются статьи с content<50 символов или пустым content,\n"
        "импортированные новости с summary<50 символов, пустым summary или содержащим 'без содержим'.\n"
        "Записи без изображения также удаляются, а при проверке битых картинок\n"
        "запросы отправляются асинхронно (httpx) с тайм‑аутами."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Удалить найденные записи. Без этого флага только отчёт.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="Сколько картинок проверять за запуск (по умолчанию 500).",
        )

    def handle(self, *args, **options):
        delete_mode = options["delete"]
        limit = options["limit"]

        # Удаление пустых статей
        art_qs = Article.objects.annotate(content_len=Length("content"))
        empty_articles = art_qs.filter(Q(content__isnull=True) | Q(content__exact="") | Q(content_len__lt=50))
        count_articles = empty_articles.count()
        if count_articles:
            if delete_mode:
                empty_articles.delete()
                self.stdout.write(self.style.ERROR(f"Удалено пустых статей: {count_articles}"))
            else:
                self.stdout.write(self.style.WARNING(f"Найдено пустых статей: {count_articles} (запустите с --delete)"))
        else:
            self.stdout.write(self.style.SUCCESS("Пустых статей нет"))

        # Удаление пустых или коротких импортированных новостей
        imp_qs = ImportedNews.objects.annotate(summary_len=Length("summary"))
        empty_imported = imp_qs.filter(
            Q(summary__isnull=True) |
            Q(summary__exact="") |
            Q(summary_len__lt=50) |
            Q(summary__icontains="без содержим")
        )
        count_imported = empty_imported.count()
        if count_imported:
            if delete_mode:
                empty_imported.delete()
                self.stdout.write(self.style.ERROR(f"Удалено импортированных новостей: {count_imported}"))
            else:
                self.stdout.write(self.style.WARNING(f"Найдено импортированных новостей: {count_imported} (запустите с --delete)"))
        else:
            self.stdout.write(self.style.SUCCESS("Пустых импортированных новостей нет"))

        # Удаляем новости без изображения
        no_image = ImportedNews.objects.filter(Q(image__isnull=True) | Q(image__exact=""))
        count_no_image = no_image.count()
        if count_no_image:
            if delete_mode:
                no_image.delete()
                self.stdout.write(self.style.ERROR(f"Удалено новостей без картинки: {count_no_image}"))
            else:
                self.stdout.write(self.style.WARNING(f"Найдено новостей без картинки: {count_no_image} (запустите с --delete)"))
        else:
            self.stdout.write(self.style.SUCCESS("Новостей без картинки нет"))

        # Проверяем битые картинки
        self.stdout.write("Проверяем битые изображения у импортированных новостей...")
        with_images = list(ImportedNews.objects.exclude(image__isnull=True).exclude(image="")[:limit])
        if with_images:
            urls = [n.image for n in with_images]
            oks = asyncio.run(_check_urls(urls))
            broken_ids = [obj.id for obj, ok in zip(with_images, oks) if not ok]
            if broken_ids:
                if delete_mode:
                    ImportedNews.objects.filter(id__in=broken_ids).delete()
                    self.stdout.write(self.style.ERROR(f"Удалено импортированных новостей с битыми картинками: {len(broken_ids)}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Найдено новостей с битыми картинками: {len(broken_ids)} (запустите с --delete)"))
            else:
                self.stdout.write(self.style.SUCCESS("Битых изображений не найдено"))
        else:
            self.stdout.write("Новостей с картинками для проверки не найдено")
