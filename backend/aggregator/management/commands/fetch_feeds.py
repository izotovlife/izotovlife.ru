#C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\izotovlife.ru\backend\aggregator\management\commands\fetch_feeds.py

from django.core.management.base import BaseCommand
from aggregator.models import Source
from aggregator.tasks import fetch_feed_for_source

class Command(BaseCommand):
    help = "Fetches news from all active RSS/Atom sources"

    def handle(self, *args, **options):
        for src in Source.objects.filter(is_active=True):
            added = fetch_feed_for_source(src)
            self.stdout.write(self.style.SUCCESS(
                f"{src.title}: добавлено {added} новостей"
            ))
