// Путь: frontend/src/components/search/SearchAutocomplete.jsx
// Назначение: Поле поиска с автокомплитом (выпадающие результаты при вводе).
// Версия v4 — мгновенный поиск через /api/news/autocomplete/
// ✅ Limit=8, debounce=200мс
// ✅ Миниатюры, источник, подсветка
// ✅ Автоматическое закрытие при клике вне

import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import css from "./SearchAutocomplete.module.css";

// ---------- Утилиты ----------
function highlightQuery(text, query) {
  if (!query || !text) return text;
  try {
    const safe = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const regex = new RegExp(safe, "gi");
    return text.replace(regex, (m) => `<mark>${m}</mark>`);
  } catch {
    return text;
  }
}

// ---------- Компонент ----------
export default function SearchAutocomplete() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const boxRef = useRef(null);
  const navigate = useNavigate();

  // --- Закрытие при клике вне блока ---
  useEffect(() => {
    const onDocClick = (e) => {
      if (!boxRef.current) return;
      if (e.target.closest(`.${css.wrap}`)) return;
      setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  // --- Поиск с задержкой (debounce) ---
  useEffect(() => {
    const delay = setTimeout(async () => {
      const value = q.trim();
      if (!value) {
        setItems([]);
        setOpen(false);
        return;
      }

      try {
        setLoading(true);
        const res = await axios.get("http://localhost:8000/api/news/autocomplete/", {
          params: { q: value, limit: 8 },
        });
        const data = res.data;
        const found = Array.isArray(data?.results)
          ? data.results
          : Array.isArray(data)
          ? data
          : [];
        setItems(found);
        setOpen(found.length > 0);
      } catch (err) {
        console.error("Ошибка автопоиска:", err);
        setItems([]);
        setOpen(false);
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(delay);
  }, [q]);

  function onSubmit(e) {
    e.preventDefault();
    if (items.length) navigate(items[0].seo_url);
    else if (q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
    setOpen(false);
  }

  const list = useMemo(() => (items?.length ? items.slice(0, 8) : []), [items]);

  return (
    <div className={css.wrap} ref={boxRef}>
      <form onSubmit={onSubmit}>
        <input
          className={css.input}
          placeholder="Поиск новостей…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onFocus={() => q && items.length && setOpen(true)}
        />
      </form>

      {open && (
        <div className={css.dropdown} role="listbox">
          {loading && <div className={css.empty}>Загрузка…</div>}
          {!loading && list.length === 0 && (
            <div className={css.empty}>Ничего не найдено</div>
          )}
          {!loading &&
            list.map((it, idx) => (
              <React.Fragment key={it.id || idx}>
                <Link
                  to={it.seo_url}
                  className={css.item}
                  onMouseDown={() => setOpen(false)}
                >
                  {it.image ? (
                    <img src={it.image} alt="" className={css.thumb} />
                  ) : (
                    <div className={css.thumbPlaceholder}>📰</div>
                  )}
                  <div className={css.textBlock}>
                    <div
                      className={css.title}
                      dangerouslySetInnerHTML={{
                        __html: highlightQuery(it.title || "(Без заголовка)", q),
                      }}
                    />
                    <div className={css.meta}>
                      {it.source_name || "Источник"}
                    </div>
                  </div>
                </Link>
                {idx < list.length - 1 && <div className={css.divider}></div>}
              </React.Fragment>
            ))}
        </div>
      )}
    </div>
  );
}
