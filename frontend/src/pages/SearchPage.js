// Путь: frontend/src/pages/SearchPage.js
// Назначение: страница поиска новостей, совместимая с API /api/news/search/

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { searchAll } from "../Api";
import "./SearchPage.css";

function formatDate(dt) {
  if (!dt) return "";
  try {
    return new Date(dt).toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dt;
  }
}

function SkeletonCard() {
  return (
    <div className="card skeleton-card">
      <div className="skeleton thumb" />
      <div className="skeleton text-line short" />
      <div className="skeleton text-line" />
      <div className="skeleton text-line long" />
    </div>
  );
}

export default function SearchPage() {
  const [sp] = useSearchParams();
  const q = (sp.get("q") || "").trim();

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const limit = 30;
  const [page, setPage] = useState(1);
  const offset = useMemo(() => (page - 1) * limit, [page]);
  const loaderRef = useRef(null);

  // сброс при новом запросе
  useEffect(() => {
    setPage(1);
    setItems([]);
  }, [q]);

  useEffect(() => {
    let cancelled = false;

    const timer = setTimeout(async () => {
      if (!q) {
        setItems([]);
        setTotal(0);
        setErr("");
        return;
      }

      setLoading(true);
      setErr("");

      try {
        const data = await searchAll(q, { limit, offset });

        // исправлено: API возвращает results и count
        const found = Array.isArray(data?.results)
          ? data.results
          : Array.isArray(data)
          ? data
          : [];

        if (!cancelled) {
          setItems((prev) => (page === 1 ? found : [...prev, ...found]));
          setTotal(data?.count || found.length);
        }
      } catch (e) {
        if (!cancelled) {
          console.error("Ошибка загрузки поиска:", e);
          setErr(e?.message || "Ошибка запроса");
          setItems([]);
          setTotal(0);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [q, offset, page]);

  // IntersectionObserver — автоподгрузка
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loading && items.length < total) {
          setPage((p) => p + 1);
        }
      },
      { threshold: 1 }
    );
    if (loaderRef.current) observer.observe(loaderRef.current);
    return () => observer.disconnect();
  }, [loading, items, total]);

  return (
    <main className="search-page">
      <h1>Поиск</h1>
      <div className="query-info">
        Запрос: <b>{q || "—"}</b>{" "}
        {total ? `(найдено: ${total})` : ""}
      </div>

      {err && <div className="error">Ошибка: {err}</div>}
      {!loading && !err && q && total === 0 && (
        <div>Ничего не найдено.</div>
      )}
      {!q && <div>Введите запрос в строке поиска вверху.</div>}

      <div className="results-grid">
        {items.map((it, idx) => (
          <article
            key={it.id || it.slug || idx}
            className="card fade-in-up"
            style={{ animationDelay: `${idx * 0.04}s` }}
          >
            {it.image ? (
              <img
                src={it.image}
                alt=""
                className="thumb"
                loading="lazy"
              />
            ) : (
              <div className="thumb placeholder">📰</div>
            )}

            <div className="card-content">
              <div className="meta">
                {it?.source_name ||
                  it?.source?.name ||
                  it?.category_display ||
                  "Источник"}
                {it.published_at
                  ? ` • ${formatDate(it.published_at)}`
                  : ""}
              </div>

              <h3>{it.title}</h3>

              {it.summary && (
                <p>
                  {it.summary.slice(0, 180)}
                  {it.summary.length > 180 ? "…" : ""}
                </p>
              )}

              {it.seo_url && (
                <Link to={it.seo_url} className="read-more">
                  Читать далее →
                </Link>
              )}
            </div>
          </article>
        ))}

        {loading &&
          Array.from({ length: 6 }).map((_, idx) => (
            <SkeletonCard key={`s-${idx}`} />
          ))}
      </div>

      {items.length < total && !loading && <div ref={loaderRef} />}
    </main>
  );
}
