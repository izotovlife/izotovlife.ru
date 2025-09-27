# backend/news/signals.py
# Назначение: Блокируем сохранение «пустых» новостей (после очистки HTML).
# Что изменено сейчас:
#   • Удалён старый импорт has_text_dict (его больше нет).
#   • Используем строгую проверку instance_has_text_strict(...).
# Примечание:
#   • Разрешаем сознательные пустые записи, если у модели выставлен allow_empty=True или force_save=True.
# Путь: backend/news/signals.py

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from . import models
from .utils.content_filters import instance_has_text_strict

# Применяем защиту к основным моделям (переименуйте, если у вас другие названия)
_PROTECT_MODELS = []
for name in ("Article", "ImportedNews"):
    if hasattr(models, name):
        _PROTECT_MODELS.append(getattr(models, name))

def _is_allowed_empty(instance) -> bool:
    """
    Лазейка для черновиков: если у инстанса есть boolean-поле allow_empty или force_save == True — пропускаем.
    Эти поля НЕ обязательны — проверка мягкая.
    """
    return bool(getattr(instance, "allow_empty", False) or getattr(instance, "force_save", False))

for Model in _PROTECT_MODELS:
    @receiver(pre_save, sender=Model)
    def _block_empty_news(sender, instance, **kwargs):
        if _is_allowed_empty(instance):
            return
        # Строго: после очистки HTML должен остаться текст (>=1 символ и >=1 слово)
        if not instance_has_text_strict(instance, min_chars=1, min_words=1):
            raise ValidationError("Запрещено сохранять новости без текста (после очистки HTML).")
