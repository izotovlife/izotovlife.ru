# Путь: backend/news/admin_forms.py
# Назначение: Формы для админки, подмена summary/content на CKEditor5 без миграций.

from django import forms
from django.conf import settings
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Article, ImportedNews


def _apply_ckeditor5(form, field_name: str):
    """Безопасно подменяет виджет поля на CKEditor5, если поле есть в форме."""
    if field_name in form.fields:
        form.fields[field_name].widget = CKEditor5Widget(
            config_name="default"
        )


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        # Берём все поля модели, чтобы ничего не потерять
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Подменяем только если поля существуют в модели
        _apply_ckeditor5(self, "summary")
        _apply_ckeditor5(self, "content")


class ImportedNewsAdminForm(forms.ModelForm):
    class Meta:
        model = ImportedNews
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _apply_ckeditor5(self, "summary")
        _apply_ckeditor5(self, "content")
