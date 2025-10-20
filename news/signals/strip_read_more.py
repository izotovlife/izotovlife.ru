# Путь: backend/news/signals/strip_read_more.py
# Назначение: Авто-очистка хвоста "читать далее" на pre_save для Article/ImportedNews.
# Ничего существующее в проекте не удаляет — это новый файл.

from django.db.models.signals import pre_save
from django.dispatch import receiver

from news.utils.text_sanitizers import strip_trailing_read_more

try:
    from news.models import Article, ImportedNews
except Exception:
    Article = None
    ImportedNews = None


def _sanitize_field(instance, field_name: str):
    if not hasattr(instance, field_name):
        return
    val = getattr(instance, field_name)
    if isinstance(val, str) and val.strip():
        new_val, changed = strip_trailing_read_more(val)
        if changed:
            setattr(instance, field_name, new_val)

@receiver(pre_save)
def strip_read_more_on_save(sender, instance, **kwargs):
    # Ограничимся нашими моделями (если обе есть в проекте)
    targets = tuple(x for x in (Article, ImportedNews) if x is not None)
    if not targets or sender not in targets:
        return

    candidate_fields = ["content", "body", "text", "summary", "lead", "description", "desc", "html"]
    for name in candidate_fields:
        _sanitize_field(instance, name)
