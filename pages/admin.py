# Путь: backend/pages/admin.py
# Назначение: Админка для статических страниц (StaticPage) с CKEditor 5.
# Обновления:
#   - Под предпросмотром кнопки: «Открыть на сайте» и «Скопировать ссылку».
#   - Контрастный live preview через CSS (без бледных инлайнов).
#   - ✅ ДОБАВЛЕНО: подключение второго CSS (admin_ckeditor5_fix.css) для контраста самой области редактора CKEditor 5.
#   - Остальной функционал (уникальный slug, дублирование, действия) сохранён.

from django.contrib import admin
from django.utils.html import format_html, strip_tags
from django.utils.safestring import mark_safe
from django.conf import settings
from django import forms
from django.utils.text import slugify

from .models import StaticPage


# ===========================
# Утилита: подобрать свободный slug
# ===========================
def ensure_unique_slug(base_slug: str, instance_pk=None) -> str:
    """
    Возвращает свободный slug. Если base_slug занят — добавляет -2, -3, ...
    instance_pk нужен, чтобы не конфликтовать с самим собой при редактировании.
    """
    base_slug = slugify(base_slug or "")
    if not base_slug:
        base_slug = "page"

    slug = base_slug
    i = 2
    qs = StaticPage.objects.all()
    if instance_pk:
        qs = qs.exclude(pk=instance_pk)

    while qs.filter(slug=slug).exists():
        slug = f"{base_slug}-{i}"
        i += 1
    return slug


# ===========================
# ФОРМА: нормализуем slug (конфликты решаем в save_model)
# ===========================
class StaticPageAdminForm(forms.ModelForm):
    class Meta:
        model = StaticPage
        fields = "__all__"

    def clean_slug(self):
        slug = self.cleaned_data.get("slug") or ""
        title = self.cleaned_data.get("title") or ""
        slug = slugify(slug) or slugify(title) or "page"
        return slug


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    form = StaticPageAdminForm

    # --- список ---
    list_display = ("title", "slug", "is_published", "updated_at", "view_link", "content_preview")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "content")
    ordering = ("-updated_at",)

    # --- форма ---
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "live_preview")
    fieldsets = (
        ("Основное", {
            "fields": ("title", "slug", "is_published", "content"),
            "description": "Заголовок и слаг формируют адрес страницы. Контент — CKEditor 5.",
        }),
        ("Предпросмотр", {
            "fields": ("live_preview",),
            "description": "Живой предпросмотр содержимого (обновляется по мере набора текста).",
        }),
        ("Метаданные", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # --- быстрые действия ---
    actions = ["action_publish", "action_unpublish", "action_duplicate"]

    @admin.action(description="✅ Опубликовать выбранные")
    def action_publish(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"Опубликовано: {updated}")

    @admin.action(description="🚫 Снять с публикации")
    def action_unpublish(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"Снято с публикации: {updated}")

    @admin.action(description="🧬 Дублировать страницу(ы)")
    def action_duplicate(self, request, queryset):
        created = 0
        for obj in queryset:
            base_slug = f"{obj.slug}-copy" if obj.slug else slugify(obj.title) + "-copy"
            new_slug = ensure_unique_slug(base_slug)
            StaticPage.objects.create(
                title=f"{obj.title} (копия)",
                slug=new_slug,
                content=obj.content,
                is_published=False,
            )
            created += 1
        self.message_user(request, f"Создано копий: {created}")

    # --- сохранение: автоподстановка уникального slug + сообщение ---
    def save_model(self, request, obj, form, change):
        original_slug = obj.slug
        new_slug = ensure_unique_slug(original_slug, instance_pk=obj.pk if change else None)
        auto_changed = (new_slug != original_slug)
        obj.slug = new_slug
        super().save_model(request, obj, form, change)
        if auto_changed:
            self.message_user(
                request,
                f"Слаг «{original_slug}» уже был занят. Автоматически установлен «{new_slug}».",
            )

    # --- служебные методы для колонок/полей ---
    def view_link(self, obj):
        if not obj.slug:
            return "—"
        site = getattr(settings, "SITE_DOMAIN", "http://127.0.0.1:8000").rstrip("/")
        url = f"{site}/pages/{obj.slug}/"
        return format_html('<a href="{}" target="_blank" rel="noopener">Открыть</a>', url)
    view_link.short_description = "Ссылка"

    def content_preview(self, obj):
        text = strip_tags(obj.content or "")
        text = " ".join(text.split())
        return (text[:117] + "…") if len(text) > 120 else text or "—"
    content_preview.short_description = "Краткое содержание"

    def live_preview(self, obj):
        """
        Контрастный предпросмотр + действия. CSS и JS подключены через Media.
        """
        initial_html = obj.content or ""
        site = getattr(settings, "SITE_DOMAIN", "http://127.0.0.1:8000").rstrip("/")
        page_url = f"{site}/pages/{obj.slug}/" if obj and obj.slug else ""
        open_btn = (
            f'<a class="lp-btn lp-btn-primary" href="{page_url}" target="_blank" rel="noopener">Открыть на сайте</a>'
            if page_url else
            '<a class="lp-btn lp-btn-disabled" href="javascript:void(0)" title="Сначала сохраните страницу с уникальным slug.">Открыть на сайте</a>'
        )
        copy_btn = (
            f'<button type="button" class="lp-btn" id="lp-copy-link" data-url="{page_url}">Скопировать ссылку</button>'
            if page_url else
            '<button type="button" class="lp-btn lp-btn-disabled" disabled>Скопировать ссылку</button>'
        )
        return mark_safe(
            f"""
            <div class="live-preview-box">
                <div id="staticpage-live-preview" class="live-preview-content">
                    {initial_html}
                </div>
            </div>
            <div class="live-preview-actions">
                {open_btn}
                {copy_btn}
                <span class="live-preview-hint">
                    Предпросмотр обновляется из редактора. Ссылка активируется после сохранения со слагом.
                </span>
            </div>
            """
        )
    live_preview.short_description = "Live preview"

    # --- подключение статики (CSS/JS) ---
    class Media:
        css = {
            "all": (
                "pages/admin_staticpage.css",     # стили блока предпросмотра
                "pages/admin_ckeditor5_fix.css",  # ✅ фиксы контраста самой области редактирования CKEditor 5
            )
        }
        js = ("pages/admin_staticpage.js",)       # скрипт live preview + копирование ссылки
