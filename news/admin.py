# Путь: backend/news/admin.py
# Назначение: Админка для категорий, статей, импортированных новостей, источников и логов.
# Особенности:
#   - Безопасные колонки: не обращаемся к полям, которых может не быть (category, source_name, homepage).
#   - Показываем значения через методы: category_display, source_display, homepage_link.
#   - Очищены list_filter/search_fields от несуществующих полей.
#   - ✅ Подключён раздел логов через admin_logs.py.
#   - ✅ В конце файла подключены глобальные admin-actions: `from . import admin_commands`.
#   - ✅ Добавлено: CKEditor5 в админке через формы ArticleAdminForm и ImportedNewsAdminForm (см. admin_forms.py).

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count

from .models import Category, Article, ImportedNews, NewsSource
from .admin_logs import *  # регистрирует разделы логов в админке
# ✅ добавлено: формы для подмены виджетов summary/content на CKEditor5 (без миграций)
from .admin_forms import ArticleAdminForm, ImportedNewsAdminForm


# ---------------------------
# ВСПОМОГАТЕЛЬНАЯ: превью картинки
# ---------------------------
def img_preview(url, width=60, height=40):
    if not url:
        return "—"
    try:
        return format_html(
            '<img src="{}" style="object-fit:cover;border-radius:6px;" width="{}" height="{}" />',
            url, width, height
        )
    except Exception:
        return "—"
img_preview.short_description = "Превью"


# ---------------------------
# CATEGORY
# ---------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "news_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # предполагаем связь ImportedNews.category_fk → Category
        # если у вас связь называется иначе — Count("importednews") замените на корректную related_name
        return qs.annotate(news_count_value=Count("importednews"))

    def news_count(self, obj):
        return obj.news_count_value
    news_count.short_description = "Кол-во новостей"

    actions = []  # оставляем включёнными, чтобы глобальные actions были видны


# ---------------------------
# ARTICLE
# ---------------------------
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    # ✅ добавлено: CKEditor5 для summary/content через форму
    form = ArticleAdminForm

    list_display = (
        "title",
        "slug",
        "category_display",   # вместо несуществующего поля category
        "status",
        "views_count",
        "image_thumb",
        "created_at",
    )
    # убрал 'category' из list_filter — он валил system check
    list_filter = ("status", )
    # оставляем только гарантированные поля
    search_fields = ("title", "slug", "summary", "content")
    date_hierarchy = "created_at"

    def image_thumb(self, obj):
        url = getattr(obj, "image", None) or getattr(obj, "image_url", None)
        return img_preview(url)
    image_thumb.short_description = "Картинка"

    def category_display(self, obj):
        """
        Безопасно достаём категорию:
        - если есть obj.category → показываем имя
        - если есть obj.category_fk → показываем имя
        - иначе '—'
        """
        cat = getattr(obj, "category", None) or getattr(obj, "category_fk", None)
        return getattr(cat, "name", "—")
    category_display.short_description = "Категория"

    actions = []  # глобальные actions подхватятся


# ---------------------------
# IMPORTED NEWS (RSS)
# ---------------------------
@admin.register(ImportedNews)
class ImportedNewsAdmin(admin.ModelAdmin):
    # ✅ добавлено: CKEditor5 для summary/content через форму
    form = ImportedNewsAdminForm

    list_display = (
        "title",
        "slug",
        "source_display",     # вместо прямого source_name
        "views_count",
        "image_thumb",
        "published_at",
    )
    # фильтруем по FK, который у нас точно есть (в проекте используем source_fk)
    list_filter = ("source_fk",)
    # оставляем только поля, которые точно есть в модели
    search_fields = ("title", "slug", "summary", "link")
    date_hierarchy = "published_at"

    def image_thumb(self, obj):
        url = getattr(obj, "image", None) or getattr(obj, "image_url", None)
        return img_preview(url)
    image_thumb.short_description = "Картинка"

    def source_display(self, obj):
        """
        Пытаемся красиво показать источник:
        - если есть obj.source_name (CharField) → его
        - иначе если есть obj.source_fk → source_fk.name
        - иначе — хостнейм из link
        """
        name = getattr(obj, "source_name", None)
        if name:
            return name
        src = getattr(obj, "source_fk", None) or getattr(obj, "source", None)
        if src and getattr(src, "name", None):
            return src.name
        # фолбэк: домен из ссылки
        link = getattr(obj, "link", "") or ""
        try:
            from urllib.parse import urlparse
            host = urlparse(link).netloc
            return host.replace("www.", "") or "Источник"
        except Exception:
            return "Источник"
    source_display.short_description = "Источник"

    actions = []  # глобальные actions подхватятся


# ---------------------------
# NEWS SOURCE
# ---------------------------
@admin.register(NewsSource)
class NewsSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "homepage_link", "logo_thumb", "is_active")
    search_fields = ("name", "slug")  # убрал 'homepage' — чтобы не валилось
    list_filter = ("is_active",)

    def logo_thumb(self, obj):
        url = getattr(obj, "logo", None) or getattr(obj, "logo_url", None)
        return img_preview(url, width=50, height=50)
    logo_thumb.short_description = "Логотип"

    def homepage_link(self, obj):
        """
        Безопасная ссылка на сайт источника:
        - проверяем по порядку: homepage, homepage_url, url, site
        """
        url = (
            getattr(obj, "homepage", None)
            or getattr(obj, "homepage_url", None)
            or getattr(obj, "url", None)
            or getattr(obj, "site", None)
        )
        if not url:
            return "—"
        return format_html('<a href="{}" target="_blank" rel="noopener">Открыть</a>', url)
    homepage_link.short_description = "Сайт"

    actions = []  # глобальные actions подхватятся


# ===========================
# ПОДКЛЮЧАЕМ ГЛОБАЛЬНЫЕ ДЕЙСТВИЯ (ОДИН РАЗ)
# ===========================
from . import admin_commands  # подключаем глобальные действия
from . import admin_logs  # регистрирует разделы логов в админке
