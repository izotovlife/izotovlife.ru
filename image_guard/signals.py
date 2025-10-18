# Путь: backend/image_guard/signals.py
# Назначение: Слушатели post_save для Article и ImportedNews.
# Если картинка бита — зачищаем поле у объекта сразу после сохранения.

from __future__ import annotations

from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver

from .utils import (
    is_url,
    check_remote_image,
    check_local_image,
    pick_image_attr,
)


# Список моделей, которые хотим «сторожить».
# Ничего не падает, если какой-то модели нет — просто пропустим.
WATCH = [
    ("news", "Article"),
    ("rssfeed", "ImportedNews"),
]


def _clean_broken_image_on_instance(instance) -> bool:
    """
    Возвращает True, если картинка была очищена.
    """
    # Предохранитель от рекурсии при повторном save()
    if getattr(instance, "_image_guard_checked", False):
        return False
    setattr(instance, "_image_guard_checked", True)

    field_name = pick_image_attr(instance)
    if not field_name:
        return False

    value = getattr(instance, field_name)
    # ImageFieldFile
    if hasattr(value, "url"):
        url = value.url
        path = getattr(value, "path", None)
        if path:
            res = check_local_image(path)
        else:
            res = check_remote_image(url)
    else:
        url = str(value)
        if not url:
            return False
        res = check_remote_image(url) if is_url(url) else None

    if res and not res.ok:
        # Очищаем картинку — НЕ удаляем новость
        try:
            setattr(instance, field_name, None)
            instance.save(update_fields=[field_name])
            return True
        except Exception:
            # Даже если что-то пошло не так — не валим процесс
            return False
    return False


# Динамически регистрируем обработчики для доступных моделей
for app_label, model_name in WATCH:
    try:
        Model = apps.get_model(app_label, model_name)
    except LookupError:
        continue

    @receiver(post_save, sender=Model, weak=False)
    def image_guard_post_save(sender, instance, created, **kwargs):
        # Проверяем на каждом save — нам важнее надёжность, чем лишний один HTTP HEAD/GET
        _clean_broken_image_on_instance(instance)
