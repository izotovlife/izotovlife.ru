# Путь: backend/news/scripts/fix_slugs.py
# Назначение: пересоздание slug для всех категорий (уникально и транслитерацией)

from news.models import Category
from django.utils.text import slugify

print("🔧 Пересоздание slug для категорий...\n")

for c in Category.objects.all():
    base_slug = slugify(c.name, allow_unicode=False)
    if not base_slug:
        base_slug = "category"

    slug = base_slug
    i = 1
    while Category.objects.filter(slug=slug).exclude(id=c.id).exists():
        i += 1
        slug = f"{base_slug}-{i}"

    old = c.slug
    c.slug = slug
    c.save()
    print(f"{c.name}: {old} → {c.slug}")

print("\n✅ Готово! Все slug пересозданы и уникальны.")
