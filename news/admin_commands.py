# Путь: backend/news/admin_commands.py
# Назначение: панель и глобальные actions для запуска management-команд.
# ✅ Работает без миграций: псевдомодель с managed=False.
# ✅ Есть "панель команд" в разделе NEWS.
# ✅ Есть глобальные actions в выпадающем меню списков моделей.
# ✅ ДОБАВЛЕНО: режим без лимита — удаление всех записей с битой картинкой (--limit=0 --delete).
#
# Изменения по сравнению с твоей версией:
#   • УДАЛЁН дублирующийся блок внизу файла с повторными импортами, второй раз объявленным
#     run_command_in_thread и повторной регистрацией действий (он мешал).
#   • Единый run_command_in_thread.
#   • В панель добавлен action_run_clean_images_unlimited (без лимита).
#   • В глобальные actions тоже добавлен пункт без лимита.

import threading
import io
import sys
from django.contrib import admin, messages
from django.core.management import call_command
from django.db import models
from news.models_logs import RSSImportLog


# ======================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: запуск команды в отдельном потоке + лог
# ======================================================
def run_command_in_thread(command_name, *args):
    """Запускает management-команду в отдельном потоке и логирует результат."""
    def _runner():
        buffer = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = buffer
        try:
            call_command(command_name, *args)
            msg = buffer.getvalue().strip() or f"Команда '{command_name}' успешно выполнена."
            RSSImportLog.objects.create(
                source_name="admin_command_runner",
                message=msg,
                level="INFO",
            )
        except Exception as e:
            RSSImportLog.objects.create(
                source_name="admin_command_runner",
                message=f"Ошибка при выполнении '{command_name}': {e}",
                level="ERROR",
            )
        finally:
            sys.stdout = sys_stdout
            print(f"[admin_command_runner] Завершено: {command_name}")

    threading.Thread(target=_runner, daemon=True).start()


# ======================================================
# ПСЕВДОМОДЕЛЬ ДЛЯ ПАНЕЛИ
# ======================================================
class CommandPanel(models.Model):
    """Псевдо-модель без таблицы (только для отображения в admin)."""
    class Meta:
        managed = False
        app_label = "news"
        verbose_name = "Панель команд"
        verbose_name_plural = "🧠 Django Commands"

    def __str__(self):
        return "Панель команд"


# ======================================================
# АДМИН-КЛАСС ПАНЕЛИ
# ======================================================
@admin.register(CommandPanel)
class CommandPanelAdmin(admin.ModelAdmin):
    """Панель управления системными командами."""
    change_list_template = None
    list_display = (
        "run_clean_images",
        "run_check_images",
        "run_clean_images_unlimited",   # ✅ новый пункт-подсказка
        "run_clean_incomplete",
        "run_clear_logs",
        "run_import_rss",
    )

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    def get_queryset(self, request):
        # фиктивный список из одного объекта
        return [CommandPanel()]

    # --- подсказки в списке (как «поля») ---
    @admin.display(description="🧹 Удалить записи с битой картинкой (limit=200) — delete=True")
    def run_clean_images(self, obj): return "Экшен ниже удалит до 200 записей с битой картинкой."

    @admin.display(description="🧪 Очистить поля битых изображений (limit=100) — без удаления")
    def run_check_images(self, obj): return "Экшен ниже очистит поля изображений, записи НЕ удаляются."

    @admin.display(description="🧹 Удалить ВСЕ записи с битой картинкой (без лимита) — delete=True")
    def run_clean_images_unlimited(self, obj): return "Экшен ниже удалит все записи с битой картинкой."

    @admin.display(description="🧼 Очистить неполные новости (без текста/обложки)")
    def run_clean_incomplete(self, obj): return "Экшен ниже удалит явно неполные записи."

    @admin.display(description="🗑 Очистить старые логи/сессии (30 дней)")
    def run_clear_logs(self, obj): return "Экшен ниже вызовет clearsessions."

    @admin.display(description="🌐 Импортировать RSS сейчас")
    def run_import_rss(self, obj): return "Экшен ниже запустит import_rss_now."

    # --- actions панели ---
    actions = [
        "action_run_clean_images",
        "action_run_check_images",
        "action_run_clean_images_unlimited",  # ✅ безлимит
        "action_run_clean_incomplete",
        "action_run_clear_logs",
        "action_run_import_rss",
    ]

    @admin.action(description="🧹 Очистить битые изображения (limit=200, delete=True)")
    def action_run_clean_images(self, request, queryset):
        run_command_in_thread("clean_broken_images", "--limit=200", "--delete")
        messages.success(request, "Удаление (до 200) записей с битой картинкой запущено.")

    @admin.action(description="🧪 Проверить битые изображения (limit=100, без удаления)")
    def action_run_check_images(self, request, queryset):
        run_command_in_thread("clean_broken_images", "--limit=100")
        messages.info(request, "Очистка полей изображений (до 100) запущена.")

    @admin.action(description="🧹 Очистить битые изображения (ВСЕ, без лимита, delete=True)")
    def action_run_clean_images_unlimited(self, request, queryset):
        # ключевой вызов: --limit=0 == без ограничения
        run_command_in_thread("clean_broken_images", "--limit=0", "--delete")
        messages.success(request, "Удаление ВСЕХ записей с битой картинкой запущено.")

    @admin.action(description="🧼 Очистить неполные новости (limit=500, delete=True)")
    def action_run_clean_incomplete(self, request, queryset):
        run_command_in_thread("clean_incomplete_news", "--limit=500", "--delete")
        messages.warning(request, "Очистка неполных новостей запущена.")

    @admin.action(description="🗑 Очистить старые логи/сессии (clearsessions)")
    def action_run_clear_logs(self, request, queryset):
        run_command_in_thread("clearsessions")
        messages.success(request, "clearsessions запущена.")

    @admin.action(description="🌐 Импортировать RSS сейчас")
    def action_run_import_rss(self, request, queryset):
        run_command_in_thread("import_rss_now")
        messages.success(request, "Импорт RSS запущен в фоне.")


# ======================================================
# ГЛОБАЛЬНЫЕ ACTIONS (чтобы были и в выпадающем меню списков моделей)
# ======================================================
@admin.action(description="🧹 Очистить битые изображения (limit=200, delete=True)")
def action_run_clean_images(modeladmin, request, queryset):
    run_command_in_thread("clean_broken_images", "--limit=200", "--delete")
    messages.success(request, "Удаление (до 200) записей с битой картинкой запущено в фоне.")

@admin.action(description="🧪 Проверить битые изображения (limit=100, без удаления)")
def action_run_check_images(modeladmin, request, queryset):
    run_command_in_thread("clean_broken_images", "--limit=100")
    messages.info(request, "Проверка и очистка полей изображений запущена в фоне.")

@admin.action(description="🧹 Очистить битые изображения (ВСЕ, без лимита, delete=True)")
def action_run_clean_images_unlimited(modeladmin, request, queryset):
    run_command_in_thread("clean_broken_images", "--limit=0", "--delete")
    messages.success(request, "Удаление ВСЕХ записей с битой картинкой запущено в фоне.")

@admin.action(description="🗑 Очистить старые логи/сессии (clearsessions)")
def action_run_clear_logs(modeladmin, request, queryset):
    run_command_in_thread("clearsessions")
    messages.success(request, "Очистка старых логов/сессий запущена в фоне.")

@admin.action(description="🌐 Импортировать RSS сейчас")
def action_run_import_rss(modeladmin, request, queryset):
    run_command_in_thread("import_rss_now")
    messages.success(request, "Импорт RSS запущен в фоне.")


# Регистрация глобальных действий
admin.site.add_action(action_run_clean_images, name="run_clean_images")
admin.site.add_action(action_run_check_images, name="run_check_images")
admin.site.add_action(action_run_clean_images_unlimited, name="run_clean_images_unlimited")  # ✅ новый пункт
admin.site.add_action(action_run_clear_logs, name="run_clear_logs")
admin.site.add_action(action_run_import_rss, name="run_import_rss")
