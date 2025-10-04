// frontend/src/components/search/SearchAutocomplete.jsx
// Назначение: Поле поиска с автокомплитом. Формирует корректные SEO-ссылки для клика:
//   • RSS (импорт): /news/:sourceSlug/:slug
//   • Article:      /news/:categorySlug/:slug
//   • Фолбэк:       /news/:slug (если чего-то не хватает, деталка разрулит)
//
// Зависимости: Api.searchAll, react-router-dom.

import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { searchAll } from "../../Api";
import css from "./SearchAutocomplete.module.css";

function isImported(item) {
  // Эвристика: у импортированных обычно есть link и нет собственного content
  return !!item?.link && !item?.content;
}
function pickSourceSlug(item) {
  return item?.source?.slug || item?.source_slug || item?.publisher_slug || null;
}
function pickCategorySlug(item) {
  return item?.category?.slug || item?.category_slug || null;
}
function buildDetailHref(item) {
  const slug = item?.slug || item?.seo_slug || item?.url_slug || null;
  if (!slug) return "#";

  if (isImported(item)) {
    const src = pickSourceSlug(item);
    if (src) return `/news/${src}/${slug}`;
    return `/news/${slug}`;
  }
  const cat = pickCategorySlug(item);
  if (cat) return `/news/${cat}/${slug}`;
  return `/news/${slug}`;
}

export default function SearchAutocomplete() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const boxRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const onDocClick = (e) => {
      if (!boxRef.current) return;
      if (!boxRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

  useEffect(() => {
    const h = setTimeout(async () => {
      if (!q.trim()) {
        setItems([]);
        return;
      }
      try {
        setLoading(true);
        const { items: found } = await searchAll(q, { limit: 10, offset: 0 });
        setItems(found);
        setOpen(true);
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(h);
  }, [q]);

  function onSubmit(e) {
    e.preventDefault();
    if (items.length) {
      const href = buildDetailHref(items[0]);
      if (href && href !== "#") {
        navigate(href);
        setOpen(false);
      }
    }
  }

  const list = useMemo(() => items.slice(0, 10), [items]);

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

      {open && list.length > 0 && (
        <div className={css.dropdown} role="listbox">
          {list.map((it) => {
            const href = buildDetailHref(it);
            return (
              <Link
                key={it.id || it.slug || Math.random()}
                to={href}
                className={css.item}
                onClick={() => setOpen(false)}
              >
                <div className={css.title}>{it.title || "Без названия"}</div>
                <div className={css.meta}>
                  {isImported(it)
                    ? (it?.source?.name || it?.source_name || "Источник")
                    : (it?.category?.name || it?.category_name || "Статья")}
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {open && !loading && list.length === 0 && (
        <div className={css.dropdown}>
          <div className={css.empty}>Ничего не найдено</div>
        </div>
      )}
    </div>
  );
}
