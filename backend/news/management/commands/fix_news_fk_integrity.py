from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from news.models import News, Category


class Command(BaseCommand):
    help = "Set author/category to NULL for News entries pointing to missing records"

    def handle(self, *args, **options):
        User = get_user_model()
        existing_users = set(User.objects.values_list("id", flat=True))
        existing_categories = set(Category.objects.values_list("id", flat=True))

        fixed_authors = []
        fixed_categories = []

        for news in News.objects.all():
            changed = False
            if news.author_id and news.author_id not in existing_users:
                fixed_authors.append(news.id)
                news.author = None
                changed = True
            if news.category_id and news.category_id not in existing_categories:
                fixed_categories.append(news.id)
                news.category = None
                changed = True
            if changed:
                news.save(update_fields=["author", "category"])

        self.stdout.write(
            f"Fixed author links: {len(fixed_authors)} - {fixed_authors}"
        )
        self.stdout.write(
            f"Fixed category links: {len(fixed_categories)} - {fixed_categories}"
        )
