# Путь: backend/news/utils/cleanup.py
# Назначение: Очистка "битых" новостей (без текста, пустые slug).

from news.models import Article, ImportedNews

def cleanup_broken_news(stdout=None):
    """
    Удаляет все новости, которые считаются 'битыми':
    - slug пустой или слишком короткий
    - пустой или слишком короткий content/summary
    """
    broken = []

    # Авторские статьи
    for a in Article.objects.all():
        if not a.slug or len(a.slug) < 3 or not a.content or len(a.content.strip()) < 50:
            broken.append(("article", a.slug))
            a.delete()

    # Импортированные RSS
    for n in ImportedNews.objects.all():
        if not n.slug or len(n.slug) < 3 or not n.summary or len(n.summary.strip()) < 50:
            broken.append(("rss", n.slug))
            n.delete()

    if stdout:
        if not broken:
            stdout.write("✓ Битых новостей не найдено")
        else:
            stdout.write(f"✖ Удалено {len(broken)} битых новостей")

    return broken
