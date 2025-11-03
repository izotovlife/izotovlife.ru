# Путь: backend/rssfeed/management/commands/probe_rss.py
# Назначение: Диагностика скорости/доступности RSS/страниц с учётом ретраев и таймаутов из rssfeed/net.py.
# Использование:
#   python manage.py probe_rss https://aif.ru/rss/all.php
#   python manage.py probe_rss https://www.aif.ru/rss/all.php
from django.core.management.base import BaseCommand

from rssfeed.net import get_rss_bytes

class Command(BaseCommand):
    help = "Пробный запрос RSS/страницы с замером таймаутов и ретраев"

    def add_arguments(self, parser):
        parser.add_argument("url", type=str, help="URL ленты или страницы")

    def handle(self, *args, **opts):
        url = opts["url"]
        data, enc, res = get_rss_bytes(url)
        self.stdout.write(self.style.SUCCESS(f"URL: {res.url}"))
        self.stdout.write(f"Status: {res.status}")
        self.stdout.write(f"Bytes: {len(data)}")
        self.stdout.write(f"Elapsed: {res.elapsed_s:.2f}s")
        self.stdout.write(f"Encoding from headers: {enc or '—'}")
        preview = data[:200].decode(enc or "utf-8", errors="replace")
        self.stdout.write("--- PREVIEW ---")
        self.stdout.write(preview)
