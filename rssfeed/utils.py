# backend/rssfeed/utils.py
# Назначение: Импорт RSS одного источника (без изменений логики удаления; учитывает архив на уровне модели).
# Путь: backend/rssfeed/utils.py

import feedparser
from dateutil import parser as dtparser
from django.utils import timezone
from news.models import ImportedNews

def import_feed_now(source):
    """
    Импортирует один RSSFeedSource.
    Возвращает количество новых записей.
    """
    parsed = feedparser.parse(source.url)
    imported = 0
    for entry in parsed.entries:
        link = entry.get('link')
        title = entry.get('title', '').strip()
        summary = entry.get('summary', '')
        published = None
        if 'published' in entry:
            try:
                published = dtparser.parse(entry.published)
            except Exception:
                published = timezone.now()
        image = ""
        if 'media_content' in entry and entry.media_content:
            image = entry.media_content[0].get('url') or ""
        elif 'links' in entry:
            for l in entry.links:
                if l.get('type','').startswith('image'):
                    image = l.get('href'); break
        if not link or not title:
            continue
        obj, created = ImportedNews.objects.get_or_create(
            link=link,
            defaults={
                'title': title[:500],
                'summary': summary,
                'image': image,
                'published_at': published,
                'source': source.name,
                'category': source.category
            }
        )
        # если запись уже была (даже в архиве), не создаём дубль; «архивность» не трогаем
        if created:
            imported += 1
    return imported
