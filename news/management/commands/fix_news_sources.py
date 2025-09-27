# backend/news/management/commands/fix_news_sources.py
# Назначение: привязывает импортированные новости к источникам NewsSource
# по домену; при отсутствии источника — создаёт его автоматически.
# Путь: backend/news/management/commands/fix_news_sources.py

from django.core.management.base import BaseCommand
from urllib.parse import urlparse
from django.utils.text import slugify
from news.models import ImportedNews, NewsSource
from unidecode import unidecode


class Command(BaseCommand):
    help = "Привязывает импортированные новости к источникам NewsSource по домену"

    def handle(self, *args, **options):
        fixed, created_sources, skipped = 0, 0, 0

        for news in ImportedNews.objects.all():
            if news.source_fk:  # уже привязана
                skipped += 1
                continue

            domain = urlparse(news.link).netloc.replace("www.", "")

            # ищем по slug
            source = NewsSource.objects.filter(slug=domain).first()

            if not source:
                # создаём новый источник
                source = NewsSource.objects.create(
                    name=domain,
                    slug=domain,
                    # логотип пока пустой, можно будет загрузить в админке
                )
                created_sources += 1
                self.stdout.write(self.style.WARNING(
                    f"🆕 Создан новый источник: {domain}"
                ))

            # привязываем новость
            news.source_fk = source
            news.save(update_fields=["source_fk"])
            fixed += 1
            self.stdout.write(self.style.SUCCESS(
                f"✅ Привязали новость {news.id} к {source.name}"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"Готово: исправлено {fixed}, создано источников {created_sources}, пропущено {skipped}"
        ))
