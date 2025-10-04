# backend/news/loghandlers.py
# Назначение: Кастомный лог-хендлер для записи ошибок резолвера slug в БД.
# Исправлено: модель импортируется лениво через apps.get_model,
# чтобы избежать ошибки AppRegistryNotReady.

import logging
import traceback
from django.apps import apps
from django.utils.timezone import now


class DBLogHandler(logging.Handler):
    """Пишет ошибки резолвера в таблицу NewsResolverLog."""

    def emit(self, record):
        try:
            # Ленивая загрузка модели
            NewsResolverLog = apps.get_model("news", "NewsResolverLog")
            if NewsResolverLog is None:
                return

            msg = self.format(record)

            NewsResolverLog.objects.create(
                created_at=now(),
                slug=getattr(record, "slug", "") or "",
                source=getattr(record, "source", "") or "",
                message=msg,
                level=record.levelname,
                traceback="".join(traceback.format_exception(
                    record.exc_info[0], record.exc_info[1], record.exc_info[2]
                )) if record.exc_info else None,
            )
        except Exception:
            # Никогда не падаем внутри логгера
            pass
