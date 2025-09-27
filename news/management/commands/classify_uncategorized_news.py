# backend/news/management/commands/classify_uncategorized_news.py
# Назначение: Классификация новостей из "Без категории" и "Лента новостей".
# Особенности:
# - безопасное создание категорий (поиск по slug и name, уникальный slug).
# - опция --limit для пакетной обработки.
# - в логах указывается ключевое слово.
# - в конце выводится статистика, включая количество "неразобранных" новостей.

from django.core.management.base import BaseCommand
from news.models import Category, Article, ImportedNews
from collections import defaultdict
from django.utils.text import slugify


CATEGORY_KEYWORDS = {
    "политика": ["политика", "парламент", "выборы", "депутат", "закон", "правительство", "президент"],
    "спорт": ["спорт", "футбол", "хоккей", "матч", "гол", "чемпионат", "игрок", "тренер"],
    "экономика": ["экономика", "доллар", "рубль", "курс", "биржа", "налоги", "инфляция", "рынок"],
    "технологии": ["технологии", "it", "гаджет", "смартфон", "компьютер", "интернет", "искусственный интеллект", "робот"],
    "культура": ["культура", "театр", "музей", "выставка", "фильм", "кино", "книга", "музыка"],
    "происшествия": ["происшествие", "дтп", "авария", "пожар", "полиция", "суд", "убийство", "катастрофа"],
}


def get_or_create_safe_category(cat_name: str) -> Category:
    """Возвращает существующую категорию или создаёт новую с уникальным slug."""
    base_slug = slugify(cat_name)
    slug = base_slug

    # 1. Ищем по slug
    cat = Category.objects.filter(slug=slug).first()
    if cat:
        return cat

    # 2. Ищем по имени
    cat = Category.objects.filter(name__iexact=cat_name).first()
    if cat:
        return cat

    # 3. Если не нашли — создаём с уникальным slug
    i = 2
    while Category.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{i}"
        i += 1

    return Category.objects.create(slug=slug, name=cat_name.capitalize())


class Command(BaseCommand):
    help = "Классифицирует новости из категорий 'Без категории' и 'Лента новостей'."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            help="Ограничить количество обрабатываемых новостей (для пакетной обработки).",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")

        uncategorized = Category.objects.filter(slug="bez-kategorii").first()
        news_feed, _ = Category.objects.get_or_create(
            slug="lenta-novostei",
            defaults={"name": "Лента новостей"}
        )

        if not uncategorized and not news_feed:
            self.stdout.write(self.style.WARNING("Нет категорий для обработки"))
            return

        stats = defaultdict(int)
        unclassified = 0
        processed_total = 0

        def classify_and_move(obj, from_cat, is_imported=False):
            nonlocal unclassified, processed_total
            processed_total += 1

            text = f"{obj.title} {getattr(obj, 'content', '') or ''} {getattr(obj, 'description', '') or ''}".lower()
            target_category = None
            matched_kw = None

            for cat_name, keywords in CATEGORY_KEYWORDS.items():
                for kw in keywords:
                    if kw in text:
                        target_category = get_or_create_safe_category(cat_name)
                        matched_kw = kw
                        break
                if target_category:
                    break

            if not target_category:
                target_category = news_feed
                matched_kw = "нет совпадений"
                unclassified += 1

            if not is_imported:
                obj.categories.set([target_category])
            else:
                obj.category = target_category

            obj.save()
            stats[target_category.name] += 1

            self.stdout.write(
                f"Новость '{obj.title[:40]}...' → {target_category.name} (ключевое слово: {matched_kw})"
            )

        # Обрабатываем обе категории
        for cat in [uncategorized, news_feed]:
            if not cat:
                continue

            articles = Article.objects.filter(categories=cat)
            imported = ImportedNews.objects.filter(category=cat)

            if limit:
                articles = articles[:limit]
                imported = imported[: max(0, limit - articles.count())]

            total = articles.count() + imported.count()
            self.stdout.write(f"\nВ категории '{cat.name}' найдено {total} новостей для обработки")

            for article in articles:
                classify_and_move(article, cat, is_imported=False)

            for item in imported:
                classify_and_move(item, cat, is_imported=True)

        # Удаляем "Без категории", если пуста
        if uncategorized:
            has_articles = Article.objects.filter(categories=uncategorized).exists()
            has_imported = ImportedNews.objects.filter(category=uncategorized).exists()
            if not has_articles and not has_imported:
                uncategorized.delete()
                self.stdout.write(self.style.SUCCESS("\nКатегория 'Без категории' удалена"))

        # Итоговая статистика
        self.stdout.write("\n====== СТАТИСТИКА ======")
        self.stdout.write(f"Всего обработано: {processed_total} новостей")
        for cat_name, count in stats.items():
            self.stdout.write(f"{cat_name}: {count} новостей")
        self.stdout.write(f"Не удалось классифицировать: {unclassified} → остались в 'Лента новостей'")
