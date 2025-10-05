# Путь: backend/news/admin_tasks.py
# Назначение: Веб-обёртка для запуска фоновых management-команд прямо из админки.

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.core.management import call_command
import io, sys, threading


def run_clean_broken_images(limit=200, delete=True, debug=False):
    """Фоновый запуск команды clean_broken_images."""
    def _target():
        stdout = io.StringIO()
        sys.stdout = stdout
        try:
            args = ["--limit", str(limit)]
            if delete:
                args.append("--delete")
            if debug:
                args.append("--debug")
            call_command("clean_broken_images", *args)
        finally:
            sys.stdout = sys.__stdout__
            print("clean_broken_images завершена")

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()


@admin.register(type("MaintenancePanel", (object,), {}))
class MaintenanceAdmin(admin.ModelAdmin):
    """Псевдо-модель для панели обслуживания."""
    change_list_template = "admin/maintenance_panel.html"

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("run-clean/", self.admin_site.admin_view(self.run_clean_view), name="run_clean_broken_images"),
        ]
        return custom_urls + urls

    def run_clean_view(self, request):
        run_clean_broken_images(limit=200, delete=True)
        messages.success(request, "🧹 Запущена очистка битых изображений (200 последних).")
        return redirect("..")
