# Путь: backend/news/utils/text_sanitizers.py
# Назначение: Утилиты для безопасной очистки текстов новостей.
# Содержит функцию strip_trailing_read_more(html_or_text): удаляет завершающее "читать далее"
# и его типичные вариации (регистр, пробелы, «...», стрелки, &nbsp; и ссылки <a>).
# Ничего ранее существовавшего в проекте не удаляет.

import re
import html
from typing import Tuple

try:
    from bs4 import BeautifulSoup, NavigableString, Tag  # bs4 уже есть в проекте
except Exception:
    BeautifulSoup = None
    NavigableString = None
    Tag = None

# Регулярка для конца строки/абзаца:
# - регистр неважен
# - допускает обычные пробелы и &nbsp;
# - допускает окончания "...", "…", "→", "»"
_READ_MORE_END_RE = re.compile(
    r"(?:\s|&nbsp;|&thinsp;)*"
    r"(?:читать)\s+(?:далее)"          # сами слова
    r"(?:\s*(?:\.{3}|…|→|»|&raquo;)*)"
    r"(?:\s|&nbsp;|&thinsp;)*$",
    re.IGNORECASE
)

# Внутренняя помощник: обрезает хвост "читать далее" у *чистого текста*.
def _strip_trailing_read_more_plain(text: str) -> Tuple[str, bool]:
    if not text:
        return text, False
    t = text
    # уберём html-сущности пробелов
    t = t.replace("\u00A0", " ").replace("&nbsp;", " ")
    # обрежем хвост, если совпадает
    m = _READ_MORE_END_RE.search(t)
    if m:
        new_text = t[:m.start()].rstrip()
        return new_text, True
    return text, False

# Основная функция: принимает как «сырой» текст, так и HTML (фрагмент).
def strip_trailing_read_more(html_or_text: str) -> Tuple[str, bool]:
    """
    Возвращает (очищенная_строка, были_ли_изменения)
    - Если на входе простой текст — режем по regex.
    - Если HTML — пытаемся аккуратно убрать последний <a> / <p> / хвостовую строку.
    """
    if not html_or_text:
        return html_or_text, False

    s = html_or_text.strip()
    # Быстрый путь: если в строке нет угловых скобок — это не HTML.
    if "<" not in s or BeautifulSoup is None:
        return _strip_trailing_read_more_plain(s)

    # HTML-путь
    soup = BeautifulSoup(s, "html.parser")

    # 1) Если последний значимый узел — абзац/ссылка/строка с "читать далее", удалим/обрежем.
    def _iter_descendants_reverse(root):
        # Идём в конец документа назад, пропуская пустяки
        for el in reversed(list(root.descendants)):
            if isinstance(el, str):
                if el.strip():
                    yield el
            else:
                # Тег
                # Пропустим теги без текста и содержимого
                if el.get_text(strip=True):
                    yield el

    changed = False

    # Сначала попробуем удалить «висящий» абзац/ссылку, состоящие только из "читать далее"
    # или хвоста «... читать далее».
    last_candidates = list(_iter_descendants_reverse(soup))
    if last_candidates:
        last = last_candidates[0]

        def text_matches_rm(txt: str) -> bool:
            # Строго проверим, что конец — "читать далее" с вариациями
            txt = html.unescape(txt or "").replace("\u00A0", " ")
            return bool(_READ_MORE_END_RE.search(txt))

        # a) Если это NavigableString (простой текст)
        if isinstance(last, NavigableString):
            txt = str(last)
            if text_matches_rm(txt):
                # Обрежем хвост у этого текстового узла
                new_txt, cut = _strip_trailing_read_more_plain(txt)
                if cut:
                    last.replace_with(new_txt)
                    changed = True

        # b) Если это тег
        elif isinstance(last, Tag):
            # Если это <a> или <p> и текст целиком про "читать далее" — удалим тег
            last_text = last.get_text(" ", strip=True)
            if _READ_MORE_END_RE.fullmatch(last_text):
                parent = last.parent
                last.extract()
                changed = True
                # Если родительский <p> опустел — удалим и его
                if parent and isinstance(parent, Tag):
                    if parent.name == "p" and not parent.get_text(strip=True):
                        parent.extract()
            else:
                # Иначе попробуем обрезать хвост в конце текста тега
                if text_matches_rm(last_text):
                    # Поищем последний текстовый узел внутри тега и обрежем его
                    for sub in reversed(list(last.descendants)):
                        if isinstance(sub, NavigableString) and sub.strip():
                            new_txt, cut = _strip_trailing_read_more_plain(str(sub))
                            if cut:
                                sub.replace_with(new_txt)
                                changed = True
                                break

    # Дополнительная страховка: если всё ещё на самом конце документа остался голый «читать далее»
    html_after = str(soup)
    final_html, cut_after = _strip_trailing_read_more_plain(html_after)
    if cut_after:
        changed = True
        return final_html.strip(), True

    return (str(soup).strip(), changed)
