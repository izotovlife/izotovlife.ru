// Путь: frontend/src/pages/NewsDetailPage.js
// Назначение: Детальная страница новости (Article или ImportedNews)
// Исправления:
//   ✅ Возвращён CSS Grid (ширины колонок стабильные).
//   ✅ Добавлен ResizeObserver: левая/правая колонки всегда равны по высоте центральной.
//   ✅ Убран useMemo (не будет ESLint-ошибок).
//   ✅ Футер остаётся на месте, адаптив сохранён.

import React, { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import DOMPurify from "dompurify";
import s from "./NewsDetailPage.module.css";

import { fetchRelated, fetchArticle, fetchNews, hitMetrics } from "../Api";

// Заглушка для отсутствующих изображений
const PLACEHOLDER =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360"><rect width="100%" height="100%" fill="#0a0f1a"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#5a6b84" font-family="Arial" font-size="18">Нет изображения</text></svg>'
  );

export default function NewsDetailPage() {
  const params = useParams();
  const [item, setItem] = useState(null);
  const [latest, setLatest] = useState([]);
  const [related, setRelated] = useState([]);
  const [error, setError] = useState(null);

  // refs для трёх колонок
  const leftRef = useRef(null);
  const mainRef = useRef(null);
  const rightRef = useRef(null);

  // === Загрузка данных ===
  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const slug = params?.slug;
        if (!slug) throw new Error("slug не найден в параметрах");

        const article = await fetchArticle(slug);
        if (cancelled) return;
        setItem(article);

        const [lastRes, relRes] = await Promise.all([
          fetchNews(1),
          fetchRelated(slug),
        ]);
        if (cancelled) return;

        setLatest(lastRes || []);
        setRelated(relRes || []);

        hitMetrics(slug).catch(() => {});
      } catch (e) {
        console.error(e);
        if (!cancelled)
          setError(e?.message || "Ошибка загрузки новости");
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [params?.slug]);

  // === Выравнивание высоты колонок под центральную (устойчиво к подгрузке изображений) ===
  useEffect(() => {
    if (!mainRef.current || !leftRef.current || !rightRef.current) return;

    const syncHeights = () => {
      const h = mainRef.current.offsetHeight;
      leftRef.current.style.height = `${h}px`;
      rightRef.current.style.height = `${h}px`;
    };

    // следим за изменением размеров центральной колонки
    const ro = new ResizeObserver(syncHeights);
    ro.observe(mainRef.current);

    // пересчитываем при ресайзе
    window.addEventListener("resize", syncHeights);

    // первичный расчёт
    syncHeights();

    return () => {
      ro.disconnect();
      window.removeEventListener("resize", syncHeights);
    };
  }, [item, latest, related]);

  // === Ошибка ===
  if (error) {
    return (
      <div className={`news-detail ${s.pageWrap}`}>
        <div className={s.main}>
          <h1 className={s.title}>Ошибка</h1>
          <div className={s.body}>{error}</div>
        </div>
      </div>
    );
  }

  if (!item) return null;

  // === Данные для рендера ===
  const imageSrc = item.image || item.cover_image || item.cover || PLACEHOLDER;
  const sourceTitle = item.source_title || item.source || "";
  const externalUrl = item.original_url || item.link || item.url || null;
  const text = item.content || item.summary || "";
  const contentHtml = DOMPurify.sanitize(text, { USE_PROFILES: { html: true } });

  return (
    <div className={`news-detail ${s.pageWrap}`}>
      {/* Левая колонка — последние новости */}
      <aside className={s.leftAside} ref={leftRef}>
        <div className={s.sectionH}>Последние новости</div>
        <div className={s.latestList}>
          {latest.map((n) => (
            <Link
              key={`l-${n.id || n.slug}`}
              to={n.seo_url || `/news/${n.slug}/`}
              className={s.latestItem}
            >
              {n.title}
            </Link>
          ))}
        </div>
      </aside>

      {/* Центральная колонка — контент */}
      <main className={s.main} ref={mainRef}>
        <h1 className={s.title}>{item.title}</h1>

        <div className={s.meta}>
          {item.pub_date_fmt || item.published_at || item.date || ""}
          {sourceTitle ? " • " + sourceTitle : ""}
        </div>

        {imageSrc && (
          <img src={imageSrc} alt={item.title} className={s.cover} />
        )}

        {(item.summary || item.content) && (
          <div
            className={s.body}
            dangerouslySetInnerHTML={{ __html: contentHtml }}
          />
        )}

        {externalUrl && (
          <div className={s.external}>
            <a
              className={s.externalLink}
              href={externalUrl}
              target="_blank"
              rel="noreferrer"
            >
              Читать в источнике →
            </a>
          </div>
        )}
      </main>

      {/* Правая колонка — похожие новости */}
      <aside className={s.rightAside} ref={rightRef}>
        <div className={s.sectionH}>Похожие новости</div>
        <div className={s.relList}>
          {related.map((n) => (
            <Link
              key={`r-${n.id || n.slug}`}
              to={n.seo_url || `/news/${n.slug}/`}
              className={s.relItem}
            >
              <img
                className={s.relThumb}
                src={n.image || PLACEHOLDER}
                alt=""
              />
              <div>
                <div className={s.relTitle}>{n.title}</div>
                <div className={s.relSource}>
                  {n.source_title || n.source || ""}
                </div>
              </div>
            </Link>
          ))}
        </div>
      </aside>
    </div>
  );
}
