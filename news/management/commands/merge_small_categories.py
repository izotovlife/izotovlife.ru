# backend/news/management/commands/merge_small_categories.py
# Назначение: Объединение маленьких категорий в "Лента новостей" и удаление пустых.
# Логика:
#   - Категории "Новости", "Общее" и с пустым названием → объединяются в "Лента новостей".
#   - Категории с 0 новостями → удаляются.
#   - Категории с <10 новостями → новости переносятся в "Лента новостей", категории удаляются.
#   - Остальные категории остаются.
#   - Safeguard: категория "Лента новостей" (slug=lenta-novostei) никогда не удаляется.

from django.core.management.base import BaseCommand
from news.models import Category, Article, ImportedNews


class Command(BaseCommand):
    help = "Объединение маленьких и пустых категорий в 'Лента новостей'"

    def handle(self, *args, **options):
        target_slug = "lenta-novostei"
        try:
            target_category = Category.objects.get(slug=target_slug)
        except Category.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                "Категория 'Лента новостей' (slug=lenta-novostei) не найдена!"
            ))
            return

        deleted_count = 0
        moved_articles = 0
        moved_imported = 0

        for category in Category.objects.exclude(id=target_category.id):
            # количество связанных статей и импортированных новостей
            article_count = Article.objects.filter(categories=category).count()
            imported_count = ImportedNews.objects.filter(category=category).count()
            total = article_count + imported_count

            # Условие для переноса
            if (
                category.name.strip() in ["Новости", "Общее", ""]
                or total == 0
                or total < 10
            ):
                # Переносим статьи
                if article_count > 0:
                    for article in Article.objects.filter(categories=category):
                        article.categories.add(target_category)
                        article.categories.remove(category)
                        moved_articles += 1

                # Переносим импортированные новости
                if imported_count > 0:
                    ImportedNews.objects.filter(category=category).update(category=target_category)
                    moved_imported += imported_count

                self.stdout.write(
                    f"Категория '{category.name}' перенесена в 'Лента новостей' (новостей: {total})"
                )
                category.delete()
                deleted_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Готово! Удалено категорий: {deleted_count}, "
            f"перенесено статей: {moved_articles}, "
            f"перенесено импортированных: {moved_imported}"
        ))
