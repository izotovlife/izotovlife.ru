# Путь: backend/news/management/commands/cleanup_no_text_news.py
# Назначение: Удаление новостей без содержания: пустой/заглушечный текст
#             (в т.ч. «Без текста», «—», «No text») при любом заголовке.
# Версия v3 — что нового:
#   • Удаляем, если ПОСЛЕ strip_tags текст короче порога (min_len) ИЛИ это стоп-фраза.
#   • НЕ требуем картинку по умолчанию (можно ужесточить флагом --require-image).
#   • Динамически собираем все CharField/TextField (summary, body, content_html, lead и т.д.).
#   • Опции:
#       --apply                выполнить удаление
#       --min-len N            порог длины очищенного текста (по умолчанию 8)
#       --only Model           Article | ImportedNews
#       --show N               показать примеры
#       --phrase "xxx"         добавить свою стоп-фразу (регистронезависимо)
#       --require-image        удалять только если у записи есть картинка
#       --debug                печатать причины отбора/отсечения
#
# Примеры:
#   python manage.py cleanup_no_text_news --debug --show 30
#   python manage.py cleanup_no_text_news --apply
#   python manage.py cleanup_no_text_news --apply --min-len 12 --require-image
#   python manage.py cleanup_no_text_news --only ImportedNews --phrase "Без текста"

from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.utils.html import strip_tags
import re, html as ihtml

DEFAULT_STOP = {
    "без текста", "нет текста", "no text", "notext", "n/a",
    "—", "–", "-", "— —", "– –",
}

IMAGE_FIELDS_HINT = ["image", "cover_image", "preview_image", "thumbnail", "photo", "picture"]

def unhtml(s: str) -> str:
    if not s:
        return ""
    s = ihtml.unescape(str(s)).replace("\xa0", " ").replace("\u202f", " ")
    s = strip_tags(s)
    s = re.sub(r"\s+", " ", s, flags=re.M).strip()
    return s

def normalize_for_stop(s: str) -> str:
    s = unhtml(s).lower()
    # уберём лишнюю пунктуацию по краям
    s = s.strip(" .!?,;:\"'()[]{}<>—–-")
    return s

def is_stop_text(s: str, stop_set) -> bool:
    ns = normalize_for_stop(s)
    if not ns:
        return True  # пустота = стоп
    if ns in stop_set:
        return True
    # «без   текста», «no   text», «n / a»
    if re.fullmatch(r"(без\s*текста|нет\s*текста|no\s*text|n\s*/\s*a|notext)", ns, flags=re.I):
        return True
    return False

def has_image(obj) -> bool:
    # 1) подсказанные поля
    for f in IMAGE_FIELDS_HINT:
        if hasattr(obj, f):
            v = getattr(obj, f)
            if v:
                s = str(v)
                if s and not s.lower().endswith("/default_news.svg"):
                    return True
    # 2) любые FileField/ImageField
    for f in obj._meta.get_fields():
        if isinstance(getattr(f, "attname_class", None), type):
            pass
        try:
            if isinstance(f, (models.FileField, models.ImageField)):
                v = getattr(obj, f.name, None)
                if v:
                    s = str(v)
                    if s and not s.lower().endswith("/default_news.svg"):
                        return True
        except Exception:
            continue
    return False

def iter_text_field_names(model):
    # сначала типичные имена, затем все текстовые поля кроме title/slug
    prefer = ["content", "body", "text", "summary", "description", "lead", "content_html", "short_text"]
    yielded = set()
    for name in prefer:
        if hasattr(model, name):
            yielded.add(name); yield name
    for f in model._meta.get_fields():
        if isinstance(f, (models.CharField, models.TextField)):
            if f.name in yielded or f.name in {"title", "slug"}:
                continue
            yielded.add(f.name)
            yield f.name

def combined_text(obj) -> str:
    parts = []
    for name in iter_text_field_names(obj.__class__):
        try:
            v = getattr(obj, name, "")
            if v:
                parts.append(str(v))
        except Exception:
            continue
    return unhtml(" ".join(parts))

def decide(obj, *, min_len: int, stop_set, require_image: bool, debug: bool):
    """
    Возвращает (is_candidate: bool, reason: str)
    """
    title = unhtml(getattr(obj, "title", "") or "")
    text = combined_text(obj)
    text_len = len(text)
    img = has_image(obj)

    # Условие наличия изображения (если требуется)
    if require_image and not img:
        return (False, "no_image") if debug else (False, "")

    # 1) Текст — стоп-фраза (или пустота) => кандидат независимо от заголовка
    if is_stop_text(text, stop_set):
        return True, "text_stop"

    # 2) Очень короткий текст (мусор/ничего)
    if text_len < min_len:
        # мягкий: достаточно короткого текста; строже включите --require-image
        return True, f"short_text<{min_len} (len={text_len})"

    # 3) Тайтл — стоп-фраза, а текст невелик (на всякий случай)
    if is_stop_text(title, stop_set) and text_len < (min_len * 2):
        return True, "title_stop + small_text"

    return (False, f"ok text_len={text_len}, img={img}") if debug else (False, "")

class Command(BaseCommand):
    help = "Удаляет новости без осмысленного текста (например, «Без текста»)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Выполнить удаление (иначе dry-run).")
        parser.add_argument("--min-len", type=int, default=8, help="Минимальная длина текста после очистки HTML.")
        parser.add_argument("--only", choices=["Article", "ImportedNews"], help="Ограничить моделью.")
        parser.add_argument("--show", type=int, default=10, help="Показать первые N кандидатов.")
        parser.add_argument("--phrase", type=str, default=None, help="Добавить пользовательскую стоп-фразу.")
        parser.add_argument("--require-image", action="store_true", help="Удалять только при наличии картинки.")
        parser.add_argument("--debug", action="store_true", help="Печатать причины отбора/исключения.")

    def handle(self, *args, **o):
        min_len = o["min_len"]
        do_apply = o["apply"]
        only = o.get("only")
        show_n = o["show"]
        require_image = o["require_image"]
        debug = o["debug"]

        # Подготовим стоп-фразы
        stop_set = set(DEFAULT_STOP)
        if o["phrase"]:
            stop_set.add(o["phrase"].lower().strip())

        from news.models import Article, ImportedNews
        targets = []
        if only in (None, "Article"):      targets.append(("Article", Article))
        if only in (None, "ImportedNews"): targets.append(("ImportedNews", ImportedNews))

        total = 0
        examples = []

        self.stdout.write(self.style.NOTICE(
            f"▶ Поиск «пустых» новостей (min_len={min_len}, require_image={require_image}) ..."
        ))

        for label, Model in targets:
            qs = Model.objects.all().only("id")  # берём id, остальное достанем при доступе
            ids = []
            cnt = 0
            for obj in qs.iterator(chunk_size=1000):
                ok, reason = decide(obj,
                                    min_len=min_len,
                                    stop_set=stop_set,
                                    require_image=require_image,
                                    debug=debug)
                if ok:
                    cnt += 1
                    ids.append(obj.pk)
                    if len(examples) < show_n:
                        title = unhtml(getattr(obj, "title", "") or "")[:80] or "—"
                        txt = combined_text(obj)[:140] or "—"
                        examples.append((label, obj.pk, reason, title, txt))
            total += cnt
            self.stdout.write(f"  • {label}: найдено {cnt}")

            if do_apply and ids:
                with transaction.atomic():
                    deleted = Model.objects.filter(pk__in=ids).delete()
                self.stdout.write(self.style.WARNING(f"    — удалено записей: {deleted[0]}"))

        self.stdout.write(self.style.SUCCESS(f"Готово. Кандидатов всего: {total}"))
        if examples:
            self.stdout.write("\nПримеры (первые {}):".format(len(examples)))
            for label, pk, reason, title, txt in examples:
                self.stdout.write(f"  [{label} #{pk}] [{reason}] «{title}» | текст: «{txt}»")
        if not do_apply:
            self.stdout.write("\nРежим dry-run. Ничего не удалено. Добавьте --apply для применения.")
