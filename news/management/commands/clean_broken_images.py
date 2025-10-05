# Путь: backend/news/management/commands/clean_broken_images.py
# Назначение: Найти записи с битой картинкой и либо очистить поля изображения, либо удалить запись.
# Обновления:
#   • run_id (UUID) для группировки логов одного запуска (source_name = "clean_broken_images#<run_id>")
#   • ГАРАНТИЯ финальной строки "Готово: ..." через try/finally
#   • Дублирование финальной строки также в source_name="clean_broken_images" (обратная совместимость)
#   • --limit=0 = без лимита
#   • --model=all|imported|article
#   • --delete — удалять записи; без флага — только чистить поля
#   • --verbose — логировать ok/cleared/deleted построчно

import os
import mimetypes
import socket
import uuid
from urllib.parse import urlparse

import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from news.models import Article, ImportedNews
try:
    from news.models_logs import RSSImportLog
except Exception:
    RSSImportLog = None

DEFAULT_LIMIT = 200
HTTP_TIMEOUT = 6.0
USER_AGENT = "Mozilla/5.0 (compatible; IzotovLifeBot/1.0; +https://izotovlife.ru)"


def _log(msg: str, source: str, level="INFO", to_console=True):
    if to_console:
        print(msg)
    if RSSImportLog:
        try:
            RSSImportLog.objects.create(source_name=source, message=msg, level=level, created_at=timezone.now())
        except Exception:
            pass


def _is_http(u: str) -> bool:
    return bool(u) and urlparse(str(u)).scheme in ("http", "https")


def _is_media_path(u: str) -> bool:
    if not u:
        return False
    v = str(u)
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    return v.startswith(media_url) or (not _is_http(v) and not v.startswith("data:"))


def _media_abspath(u: str) -> str:
    media_root = getattr(settings, "MEDIA_ROOT", "")
    media_url = getattr(settings, "MEDIA_URL", "/media/")
    v = str(u)
    if v.startswith(media_url):
        v = v[len(media_url):]
    return os.path.join(media_root, v.lstrip("/"))


def _http_image_ok(url: str) -> bool:
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    try:
        r = requests.head(url, headers=headers, timeout=HTTP_TIMEOUT, allow_redirects=True)
        if r.status_code == 405:
            raise requests.RequestException("HEAD not allowed")
        if 200 <= r.status_code < 300 and r.headers.get("Content-Type", "").startswith("image/"):
            return True
        r = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT, stream=True)
        if 200 <= r.status_code < 300 and r.headers.get("Content-Type", "").startswith("image/"):
            for chunk in r.iter_content(512):
                if chunk:
                    return True
        return False
    except (requests.RequestException, socket.timeout):
        return False


def _local_image_ok(path_or_url: str) -> bool:
    try:
        p = _media_abspath(path_or_url)
        return os.path.isfile(p) and os.path.getsize(p) > 0
    except Exception:
        return False


def _image_is_broken(value: str) -> bool:
    if not value:
        return False
    v = str(value)
    if _is_http(v):
        return not _http_image_ok(v)
    if _is_media_path(v):
        return not _local_image_ok(v)
    if v.startswith("data:"):
        mime = v.split(";")[0].replace("data:", "")
        return not mime.startswith("image/")
    mime_guess, _ = mimetypes.guess_type(v)
    if mime_guess and not mime_guess.startswith("image/"):
        return True
    return not _local_image_ok(v)


def _image_fields(obj):
    names = ["image", "image_url", "thumbnail", "thumbnail_url", "cover", "cover_url", "logo", "logo_url"]
    return [n for n in names if hasattr(obj, n)]


class Command(BaseCommand):
    help = "Очистить поля с битой картинкой или удалить записи (ImportedNews/Article)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                            help="Сколько записей проверить (0 = без лимита; default: 200)")
        parser.add_argument("--model", choices=["imported", "article", "all"], default="all")
        parser.add_argument("--delete", action="store_true", help="Удалять записи с битой картинкой.")
        parser.add_argument("--verbose", action="store_true")
        parser.add_argument("--run-id", type=str, default="", help="Идентификатор запуска (опционально).")

    def handle(self, *args, **opts):
        limit = opts["limit"]
        scope = opts["model"]
        do_delete = opts["delete"]
        verbose = opts["verbose"]
        run_id = opts["run_id"].strip() or uuid.uuid4().hex[:12]

        # Два канала логирования:
        #  - детальный поток — в source "clean_broken_images#<run_id>"
        #  - итоговая сводка дополнительно дублируется в "clean_broken_images"
        source = f"clean_broken_images#{run_id}"
        summary_source = "clean_broken_images"

        checked = fixed = deleted = 0
        started_at = timezone.now()

        # Стартовая запись
        _log(
            f"Старт: model={scope}, limit={'∞' if limit == 0 else limit}, delete={do_delete}, verbose={verbose}, run_id={run_id}",
            source
        )

        try:
            def process(qs, label):
                nonlocal checked, fixed, deleted
                processed = 0
                for obj in qs.iterator():
                    if limit > 0 and processed >= limit:
                        break

                    fields = _image_fields(obj)
                    if not fields:
                        continue

                    values = {f: getattr(obj, f) for f in fields if getattr(obj, f, None)}
                    if not values:
                        continue

                    broken = [f for f, val in values.items() if _image_is_broken(val)]
                    if not broken:
                        if verbose:
                            _log(f"[{label}] ok id={obj.pk}", source)
                        checked += 1
                        processed += 1
                        continue

                    if do_delete:
                        pk = obj.pk
                        obj.delete()
                        deleted += 1
                        checked += 1
                        processed += 1
                        _log(f"[{label}] ❌ deleted id={pk} (broken: {', '.join(broken)})", source, level="WARNING")
                    else:
                        for bf in broken:
                            try:
                                setattr(obj, bf, None)
                            except Exception:
                                setattr(obj, bf, "")
                        try:
                            obj.save(update_fields=list(set(broken)))
                        except Exception:
                            obj.save()
                        fixed += 1
                        checked += 1
                        processed += 1
                        _log(f"[{label}] 🧹 cleared id={obj.pk} fields={', '.join(broken)}", source)

            if scope in ("all", "imported"):
                process(ImportedNews.objects.order_by("-published_at", "-id"), "ImportedNews")
            if scope in ("all", "article"):
                process(Article.objects.order_by("-created_at", "-id"), "Article")

        finally:
            lim_text = "∞" if limit == 0 else str(limit)
            finished_at = timezone.now()
            delta = (finished_at - started_at).total_seconds()
            summary = (
                f"Готово: проверено {checked}, очищено {fixed}, удалено {deleted}. "
                f"(limit={lim_text}, model={scope}, delete={do_delete}, run_id={run_id}, took={int(delta)}s)"
            )
            # финал в детальный канал запуска
            _log(summary, source)
            # дублируем финал в общий канал для обратной совместимости фильтров
            _log(summary, summary_source)
