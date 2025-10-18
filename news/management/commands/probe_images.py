# Путь: backend/news/management/commands/probe_images.py
# Назначение: Диагностика “битых” иллюстраций по категориям. НИЧЕГО в БД не меняет.
#
# Что нового (ускорение и стабильность):
#   ✅ Параллельная проверка URL (ThreadPoolExecutor) — десятки раз быстрее
#   ✅ Короткие таймауты по умолчанию: 3s connect / 5s read (настраивается флагами)
#   ✅ Кэш результатов по URL (не дергаем одинаковые ссылки)
#   ✅ Прогресс-лог каждые N элементов и аккуратное завершение по Ctrl+C
#   ✅ Флаги CLI: --limit, --workers, --timeout-connect, --timeout-read
#
# Запуск (быстрый прогон):
#   python manage.py probe_images --workers 16 --limit 2000
#
# Полный прогон:
#   python manage.py probe_images --workers 24
#
# Примечание: предупреждение про CKEditor можно игнорировать — оно не влияет.

import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from urllib.parse import urlparse

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import (
    ForeignKey,
    ManyToManyField,
    ImageField,
    FileField,
    CharField,
    TextField,
)

import requests

# --------- сетевые вспомогалки ---------
def _flip_scheme(url: str) -> str | None:
    if not url or not isinstance(url, str):
        return None
    try:
        u = urlparse(url)
        if u.scheme == "http":
            return url.replace("http://", "https://", 1)
        if u.scheme == "https":
            return url.replace("https://", "http://", 1)
    except Exception:
        pass
    return None


def _headers(url: str) -> dict:
    try:
        u = urlparse(url)
        ref = f"{u.scheme}://{u.netloc}/" if u.scheme and u.netloc else ""
    except Exception:
        ref = ""
    h = {"User-Agent": "IzotovLife-Probe/1.4 (+https://izotovlife.ru)"}
    if ref:
        h["Referer"] = ref
    return h


def _looks_image(resp: requests.Response) -> bool:
    ct = (resp.headers.get("Content-Type") or "").lower().split(";")[0].strip()
    return ct.startswith("image/")


def _probe(url: str, timeout=(3.0, 5.0)) -> tuple[bool, str]:
    """
    Вернёт (ok, reason).
    ok=False и reason с текстом — если что-то не так.
    """
    if not url or not isinstance(url, str):
        return False, "empty-url"

    s = url.strip()
    if s.startswith("data:"):
        return False, "data-uri"  # встроенные data: пропускаем

    # 1) HEAD
    try:
        r = requests.head(s, timeout=timeout, headers=_headers(s), allow_redirects=True)
        if 200 <= r.status_code < 300 and _looks_image(r):
            return True, "ok-head"
    except Exception:
        pass

    # 2) GET с ограничением объёма
    reason = ""
    try:
        with requests.get(s, stream=True, timeout=timeout, headers=_headers(s), allow_redirects=True) as r:
            if 200 <= r.status_code < 300 and _looks_image(r):
                total = 0
                for chunk in r.iter_content(8192):
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > 32768:  # 32 КБ достаточно, чтобы убедиться
                        break
                return True, "ok-get"
            reason = f"http-{r.status_code}"
    except Exception as e:
        reason = f"err-{type(e).__name__}"

    # 3) flip http↔https
    alt = _flip_scheme(s)
    if alt:
        try:
            with requests.get(alt, stream=True, timeout=timeout, headers=_headers(alt), allow_redirects=True) as r:
                if 200 <= r.status_code < 300 and _looks_image(r):
                    return True, "ok-alt-scheme"
                return False, f"alt-http-{r.status_code}"
        except Exception as e:
            return False, f"alt-err-{type(e).__name__}"

    return False, reason or "unknown"


# --------- работа с моделями/полями ---------
LIKELY_IMAGE_NAME_PARTS = ("image", "cover", "preview", "thumb", "photo", "picture", "pic", "banner", "poster", "top")
LIKELY_VIDEO_NAME_PARTS = ("video", "mp4", "webm", "mov")


def _collect_candidate_models():
    """
    Находим модели новостей. По умолчанию: news.Article и (если есть) ImportedNews — в любом app_label.
    Также подбираем по имени из всех приложений (Article/News/ImportedNews/Item/RssItem).
    """
    candidates = []

    # Явные попытки
    for app_label, model_name in [
        ("news", "Article"),
        ("news", "ImportedNews"),
        ("rssfeed", "ImportedNews"),
    ]:
        try:
            m = apps.get_model(app_label, model_name)
            if m is not None:
                candidates.append((app_label, model_name, m))
        except LookupError:
            pass

    # Поиск по всем моделям — на случай нестандартных имён/приложений
    wanted_names = {"article", "news", "importednews", "rssitem", "item"}
    for m in apps.get_models():
        name = m.__name__.lower()
        if name in wanted_names and (m._meta.app_label, m.__name__) not in [(a, n) for a, n, _ in candidates]:
            candidates.append((m._meta.app_label, m.__name__, m))

    # Удалим дубли по (app_label, ModelName)
    seen = set()
    uniq = []
    for app_label, model_name, m in candidates:
        key = (app_label, model_name)
        if key not in seen:
            seen.add(key)
            uniq.append((app_label, model_name, m))
    return uniq


def _build_category_maps(Category):
    by_id = {c.pk: (getattr(c, "slug", None) or getattr(c, "name", None) or str(c.pk)) for c in Category.objects.all().only("id", "slug", "name")}
    name_to_slug = {}
    slug_set = set()
    for c in Category.objects.all().only("id", "slug", "name"):
        slug = (getattr(c, "slug", "") or "").strip().lower()
        name = (getattr(c, "name", "") or "").strip().lower()
        if slug:
            slug_set.add(slug)
        if name:
            name_to_slug[name] = slug or name
    return by_id, name_to_slug, slug_set


def _find_category_link(model, Category):
    """
    Возвращает (mode, field_name): 'fk' | 'm2m' | 'slug' | (None, None)
    """
    for f in model._meta.get_fields():
        if isinstance(f, ForeignKey) and getattr(f, "remote_field", None) and f.remote_field.model == Category:
            return "fk", f.name
        if isinstance(f, ManyToManyField) and getattr(f, "remote_field", None) and f.remote_field.model == Category:
            return "m2m", f.name

    # строковое поле с названием вроде category/category_slug
    for f in model._meta.get_fields():
        if isinstance(f, (CharField, TextField)) and "category" in f.name.lower():
            return "slug", f.name

    return None, None


def _guess_image_fields(model):
    """
    Возвращает список имён полей с изображениями.
    Правила:
      • Все ImageField — берём.
      • FileField берём, только если имя поля "похоже" на изображение и НЕ похоже на видео.
      • Строковые поля с “говорящими” именами — в конец списка.
    """
    fields = model._meta.get_fields()
    candidates = []

    # 1) ImageField — приоритет
    for f in fields:
        if isinstance(f, ImageField):
            candidates.append(f.name)

    # 2) FileField, но не видео
    for f in fields:
        if isinstance(f, FileField) and not isinstance(f, ImageField):
            lname = f.name.lower()
            if any(part in lname for part in LIKELY_VIDEO_NAME_PARTS):
                continue
            if any(part in lname for part in LIKELY_IMAGE_NAME_PARTS):
                candidates.append(f.name)

    # 3) Строковые поля с "говорящими" именами
    for f in fields:
        if isinstance(f, (CharField, TextField)):
            lname = f.name.lower()
            if any(part in lname for part in LIKELY_IMAGE_NAME_PARTS):
                candidates.append(f.name)

    # убрать дубли, сохранить порядок
    seen = set()
    out = []
    for name in candidates:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def _extract_url_from_field_value(v) -> str:
    """
    Превращает значение поля в строковый URL, если возможно.
      - FieldFile (ImageField/FileField): безопасно берём .url ТОЛЬКО если есть .name; .url оборачиваем в try/except
      - str: как есть (strip)
      - иначе: ""
    ВАЖНО: доступ к .url у пустого FieldFile поднимает ValueError — ловим и возвращаем "".
    """
    if v is None:
        return ""
    # FileField/ImageField → FieldFile
    if hasattr(v, "name") or hasattr(v, "url"):
        name = getattr(v, "name", "") or ""
        if not name:
            return ""
        try:
            url = getattr(v, "url", None)
            if isinstance(url, str) and url:
                return url.strip()
        except Exception:
            return ""
        return ""
    if isinstance(v, str):
        return v.strip()
    return ""


def _first_non_empty_image_url(obj, ordered_fields):
    """Идём по списку полей и возвращаем первый непустой URL."""
    for name in ordered_fields:
        try:
            v = getattr(obj, name, "")
        except Exception:
            continue
        url = _extract_url_from_field_value(v)
        if url:
            return url
    return ""


def _normalize_possible_slug(text: str) -> str:
    """
    Делает из произвольной строки возможный slug:
      - берём последний сегмент после '/'
      - приводим к нижнему регистру, обрезаем пробелы/слеши
    """
    if not text:
        return ""
    s = str(text).strip().lower()
    s = s.strip("/")
    if "/" in s:
        s = s.split("/")[-1]
    return s


# --------- кэш результатов и параллельная обёртка ---------
_probe_cache: dict[str, tuple[bool, str]] = {}
_probe_lock = Lock()

def _probe_cached(url: str, timeout_tuple: tuple[float, float]) -> tuple[bool, str]:
    if not url:
        return False, "empty-url"
    # быстрый путь без блокировки
    cached = _probe_cache.get(url)
    if cached is not None:
        return cached
    # защищаем от гонок
    with _probe_lock:
        cached = _probe_cache.get(url)
        if cached is not None:
            return cached
        res = _probe(url, timeout=timeout_tuple)
        _probe_cache[url] = res
        return res


class Command(BaseCommand):
    help = "Пробегает модели новостей и собирает отчёт по «битым» изображениям (по категориям). Поля определяются автоматически."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Ограничить количество записей на модель (для быстрого прогона).")
        parser.add_argument("--workers", type=int, default=12, help="Количество потоков для сетевых проверок (по умолчанию 12).")
        parser.add_argument("--timeout-connect", type=float, default=3.0, help="Таймаут соединения (сек).")
        parser.add_argument("--timeout-read", type=float, default=5.0, help="Таймаут чтения (сек).")

    def handle(self, *args, **options):
        limit = options.get("limit")
        workers = max(1, int(options.get("workers") or 12))
        to_conn = float(options.get("timeout_connect") or 3.0)
        to_read = float(options.get("timeout_read") or 5.0)
        timeout_tuple = (to_conn, to_read)

        # --- подготовка путей ---
        out_dir = os.path.join(getattr(settings, "MEDIA_ROOT", "media"), "cache")
        os.makedirs(out_dir, exist_ok=True)
        csv_path = os.path.join(out_dir, "image_report.csv")

        # --- Category ---
        try:
            Category = apps.get_model("news", "Category")
        except LookupError:
            self.stderr.write(self.style.ERROR("Не найдена модель news.Category — без неё нельзя собрать статистику."))
            return

        id_to_slug, name_to_slug, slug_set = _build_category_maps(Category)

        # --- какие модели сканируем ---
        models = _collect_candidate_models()
        if not models:
            self.stderr.write(self.style.ERROR("Не нашёл ни одной модели новостей (ни news.Article, ни ImportedNews и т.п.)."))
            return

        # --- агрегатор статистики ---
        stats = {}  # slug -> {"ok": 0, "broken": 0, "samples": []}
        rows = []
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

        def bump(slug: str, ok: bool, sample: dict):
            if not slug:
                slug = "unknown"
            d = stats.setdefault(slug, {"ok": 0, "broken": 0, "samples": []})
            if ok:
                d["ok"] += 1
            else:
                d["broken"] += 1
                if len(d["samples"]) < 10:
                    d["samples"].append(sample)

        # --- собираем задачи (без сети) ---
        all_tasks = []  # список словарей с подготовленными данными
        for app_label, model_name, Model in models:
            self.stdout.write(self.style.NOTICE(f"Сканирую {app_label}.{model_name} ..."))

            # связь с Category
            mode, cat_field = _find_category_link(Model, Category)
            if not mode:
                self.stdout.write(f"  ⚠ Связь с Category не обнаружена → категории будут 'unknown'.")
            else:
                self.stdout.write(f"  ✅ Связь с Category: {mode} ({cat_field})")

            # поля изображений
            img_fields = _guess_image_fields(Model)
            if not img_fields:
                self.stdout.write(f"  ⚠ Не нашёл ни одного поля, похожего на изображение.")
            else:
                self.stdout.write(f"  ✅ Поля изображений: {', '.join(img_fields)}")

            slug_field = "slug" if any(f.name == "slug" for f in Model._meta.get_fields()) else None

            cnt = 0
            qs = Model.objects.all()
            if limit:
                qs = qs[:limit]
            for obj in qs.iterator(chunk_size=500):
                # категория → slug
                cat_slug_value = "unknown"
                if mode == "fk":
                    try:
                        cat_id = getattr(obj, f"{cat_field}_id", None)
                        if cat_id in id_to_slug:
                            cat_slug_value = id_to_slug[cat_id]
                    except Exception:
                        pass
                elif mode == "m2m":
                    try:
                        ids = list(getattr(obj, cat_field).values_list("id", flat=True)[:3])
                        if ids:
                            cat_slug_value = id_to_slug.get(ids[0], "unknown")
                    except Exception:
                        pass
                elif mode == "slug":
                    try:
                        raw = getattr(obj, cat_field, "") or ""
                        norm = _normalize_possible_slug(raw)
                        if norm in slug_set:
                            cat_slug_value = norm
                        else:
                            cat_slug_value = name_to_slug.get(norm, "unknown")
                    except Exception:
                        pass

                # URL изображения
                src = _first_non_empty_image_url(obj, img_fields)

                model_tag = f"{app_label}.{model_name}"
                obj_slug = getattr(obj, slug_field, None) if slug_field else None
                obj_slug = obj_slug or f"id-{getattr(obj, 'pk', None)}"

                all_tasks.append({
                    "model_tag": model_tag,
                    "pk": getattr(obj, "pk", None),
                    "obj_slug": obj_slug,
                    "cat_slug": cat_slug_value,
                    "src": src,
                })
                cnt += 1

            self.stdout.write(f"  → подготовлено записей: {cnt}")

        if not all_tasks:
            self.stdout.write(self.style.WARNING("Нет записей для проверки."))
            return

        # --- параллельная проверка уникальных URL ---
        unique_urls = [t["src"] for t in all_tasks if t["src"]]
        unique_urls = list(dict.fromkeys(unique_urls))  # preserve order + dedup
        self.stdout.write(f"\nНачинаю сетевую проверку: {len(all_tasks)} записей, {len(unique_urls)} уникальных URL, workers={workers}, timeout={timeout_tuple}s")
        start = time.time()

        url_results: dict[str, tuple[bool, str]] = {}
        processed = 0
        step_log = max(25, len(unique_urls) // 40)  # ~40 логов максимум

        try:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = {ex.submit(_probe_cached, u, timeout_tuple): u for u in unique_urls}
                for fut in as_completed(futures):
                    u = futures[fut]
                    try:
                        ok, reason = fut.result()
                    except Exception as e:
                        ok, reason = False, f"err-{type(e).__name__}"
                    url_results[u] = (ok, reason)
                    processed += 1
                    if processed % step_log == 0 or processed == len(unique_urls):
                        elapsed = time.time() - start
                        self.stdout.write(f"  • проверено {processed}/{len(unique_urls)} URL  ({elapsed:.1f}s)")
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nОстановлено пользователем. Запишу частичные результаты..."))

        # --- сбор строк отчёта ---
        for t in all_tasks:
            src = t["src"]
            if not src:
                ok, reason = False, "empty-url"
            else:
                ok, reason = url_results.get(src, (False, "no-result"))
            bump(t["cat_slug"], ok, {"model": t["model_tag"], "id": t["pk"], "slug": t["obj_slug"], "reason": reason, "src": src})
            rows.append([
                t["model_tag"],
                t["pk"],
                t["cat_slug"],
                t["obj_slug"],
                "OK" if ok else "BROKEN",
                reason,
                src,
            ])

        # --- запись CSV ---
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["generated_at", now])
            w.writerow(["workers", workers, "timeout_connect", to_conn, "timeout_read", to_read, "limit", limit or "∞"])
            w.writerow([])
            w.writerow(["model", "id", "category_slug", "news_slug", "status", "reason", "src"])
            w.writerows(rows)

        # --- сводка по категориям ---
        self.stdout.write(self.style.SUCCESS(f"\nОтчёт сохранён: {csv_path}\n"))
        for slug, d in sorted(stats.items(), key=lambda kv: kv[0]):
            total = d["ok"] + d["broken"]
            if total == 0:
                continue
            bad_pct = (d["broken"] * 100.0) / total
            self.stdout.write(f"[{slug}] ok={d['ok']} broken={d['broken']}  ({bad_pct:.1f}%)")
            if d["samples"]:
                self.stdout.write("  Примеры BROKEN:")
                for s in d["samples"]:
                    self.stdout.write(f"    - {s['model']}:{s['id']} / {s['slug']} → {s['reason']}")
        self.stdout.write(self.style.SUCCESS("\nГотово."))
