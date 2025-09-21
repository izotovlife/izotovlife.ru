// frontend/src/pages/SearchPage.js
// Оптимизация: debounce для запросов, загрузка пачками по 30-50.
// Путь: frontend/src/pages/SearchPage.js

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { searchAll } from "../Api";

function formatDate(dt) {
  if (!dt) return "";
  try {
    return new Date(dt).toLocaleString("ru-RU");
  } catch {
    return dt;
  }
}

// --- Компонент скелетона карточки ---
function SkeletonCard() {
  return (
    <div
      style={{
        border: "1px solid #1f2937",
        borderRadius: 12,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div className="skeleton" style={{ height: 150, width: "100%" }} />
      <div
        style={{
          padding: 12,
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        <div className="skeleton" style={{ height: 14, width: "60%" }} />
        <div className="skeleton" style={{ height: 20, width: "90%" }} />
        <div className="skeleton" style={{ height: 16, width: "80%" }} />
      </div>
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
        if (!cancelled) {
          setItems((prev) =>
            page === 1 ? data.items : [...prev, ...data.items]
          );
          setTotal(data.total);
        }
      } catch (e) {
        if (!cancelled) {
          setErr(e?.message || "Ошибка запроса");
          setItems([]);
          setTotal(0);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 300); // debounce 300 мс

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [q, offset, page, limit]);

  // IntersectionObserver
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
    <main style={{ maxWidth: 1100, margin: "16px auto", padding: "0 16px" }}>
      <h1 style={{ margin: "0 0 12px" }}>Поиск</h1>
      <div style={{ color: "#666", marginBottom: 16 }}>
        Запрос: <b>{q || "—"}</b>{" "}
        {total ? `(найдено: ${total})` : ""}
      </div>

      {err && <div style={{ color: "crimson" }}>Ошибка: {err}</div>}
      {!loading && !err && q && total === 0 && <div>Ничего не найдено.</div>}
      {!q && <div>Введите запрос в строке поиска вверху.</div>}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: 16,
        }}
      >
        {items.map((it) => (
          <article
            key={it.id || it.slug || it.source_url}
            style={{
              border: "1px solid #1f2937",
              borderRadius: 12,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
            }}
          >
            {it.image ? (
              <img
                src={it.image}
                alt=""
                style={{ width: "100%", height: 150, objectFit: "cover" }}
                loading="lazy"
              />
            ) : null}

            <div
              style={{
                padding: 12,
                display: "flex",
                flexDirection: "column",
                gap: 8,
              }}
            >
              <div style={{ fontSize: 14, color: "#888" }}>
                {it.source || (it.type === "rss" ? "RSS" : "Автор")}
                {it.published_at ? ` • ${formatDate(it.published_at)}` : ""}
              </div>

              <h3 style={{ margin: 0, fontSize: 18, lineHeight: 1.25 }}>
                {it.title}
              </h3>

              {it.type === "rss" && it.source_url ? (
                <a
                  href={it.source_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    color: "#1a73e8",
                    fontSize: 14,
                    textDecoration: "underline",
                  }}
                >
                  Читать в источнике →
                </a>
              ) : it.type === "article" && it.slug ? (
                <Link
                  to={`/article/${it.slug}`}
                  style={{
                    color: "#1a73e8",
                    fontSize: 14,
                    textDecoration: "underline",
                  }}
                >
                  Подробнее →
                </Link>
              ) : null}

              {it.summary ? (
                <p style={{ margin: 0, color: "#ccc" }}>
                  {it.summary.slice(0, 220)}
                  {it.summary.length > 220 ? "…" : ""}
                </p>
              ) : null}
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
