# пример: backend/news/importers/your_rss_importer.py
# …ваш цикл по записям источника…
from news.importers.hooks import validate_before_save, SkipEmptyNews

for entry in feed_entries:
    raw = map_entry_to_dict(entry)  # dict с полями title, content/description, link, image и т.д.

    try:
        # 1) Сторож на входе — выкинет «только заголовок», слабый текст, заблокированные домены
        validate_before_save(raw)
        # 2) (опционально) ваши дополнительные проверки
        # 3) Сохранение
        ImportedNews.objects.create(**raw)

    except SkipEmptyNews as e:
        logger.info(str(e))  # запишем причину и перейдём к следующей
        continue
