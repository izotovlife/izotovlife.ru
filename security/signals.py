# Путь: backend/security/signals.py
# Назначение: Сигналы приложения security. Очищаем флаг доступа к внутренней админке при logout.
# Действие: при user_logged_out удаляет ключ сессии settings.SECURITY_ADMIN_SESSION_KEY (по умолчанию — "admin_internal_allowed").

from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.conf import settings

# Совместимость: берём ключ из настроек, иначе дефолт.
SESSION_FLAG_KEY = getattr(settings, "SECURITY_ADMIN_SESSION_KEY", "admin_internal_allowed")

@receiver(user_logged_out)
def clear_admin_flag_on_logout(sender, request, user, **kwargs):
    if not request:
        return
    try:
        session = getattr(request, "session", None)
        if session and SESSION_FLAG_KEY in session:
            del session[SESSION_FLAG_KEY]
    except Exception:
        # Не шумим — этот хук не должен ломать logout
        pass
