# Путь: backend/news/management/commands/check_news_integrity.py
# Назначение: Проверка целостности новостей (Article и ImportedNews).
# Проходит по всем slug в базе и проверяет, доступны ли они через API.
# Выводит отчёт: сколько всего, сколько битых, список slug с ошибками.

from django.core.management.base import BaseCommand
from django.urls import reverse
from django.test import Client

from news.models import Article, ImportedNews


class Command(BaseCommand):
    help = "Сканирует все Article и ImportedNews и проверяет, не возвращают ли они 404 через API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-broken",
            action="store_true",
            help="Удалять битые записи из базы.",
        )

    def handle(self, *args, **options):
        client = Client()
        broken = []

        # Проверка Article
        self.stdout.write("Проверка Article...")
        for a in Article.objects.all():
            url = reverse("news:article_detail", args=[a.slug])
            resp = client.get(url)
            if resp.status_code == 404:
                broken.append(("article", a.slug))
                self.stdout.write(self.style.ERROR(f"  ✖ Article slug={a.slug} → 404"))

        # Проверка ImportedNews
        self.stdout.write("Проверка ImportedNews...")
        for n in ImportedNews.objects.all():
            url = reverse("news:rss_detail", args=[n.slug])
            resp = client.get(url)
            if resp.status_code == 404:
                broken.append(("rss", n.slug))
                self.stdout.write(self.style.ERROR(f"  ✖ ImportedNews slug={n.slug} → 404"))

        if not broken:
            self.stdout.write(self.style.SUCCESS("Все записи доступны."))
            return

        self.stdout.write(self.style.WARNING(f"Найдено битых: {len(broken)}"))
        for t, slug in broken:
            self.stdout.write(f"  - {t}: {slug}")

        if options["delete_broken"]:
            self.stdout.write(self.style.WARNING("Удаляем битые..."))
            for t, slug in broken:
                if t == "article":
                    Article.objects.filter(slug=slug).delete()
                else:
                    ImportedNews.objects.filter(slug=slug).delete()
            self.stdout.write(self.style.SUCCESS("Удаление завершено."))
