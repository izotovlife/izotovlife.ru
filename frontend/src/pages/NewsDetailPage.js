// Путь: frontend/src/pages/NewsDetailPage.js
import React, { useEffect, useState, useRef } from "react";
import { useParams, Link, useNavigate, useLocation } from "react-router-dom";
import DOMPurify from "dompurify";
import s from "./NewsDetailPage.module.css";
import {
  fetchRelated,
  fetchArticle,
  fetchImportedNews,
  fetchNews,
  hitMetrics,
  resolveNews,
} from "../Api";

// ---------- утилиты ----------
function getHostname(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch { return ""; }
}
function sourceDisplay(n) {
  return n?.source?.name || n?.source_name || getHostname(n?.link || "") || "Источник";
}
// глобальный кэш на вкладку, переживает перемонтирование компонента
function getLoadedSet() {
  if (!window.__loadedSlugs) window.__loadedSlugs = new Set();
  return window.__loadedSlugs;
}

export default function NewsDetailPage() {
  // читаем ВСЕ параметры — так мы понимаем тип прямо из URL
  const { category, source, slug } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [news, setNews] = useState(null);
  const [related, setRelated] = useState([]);
  const [latest, setLatest] = useState([]);
  const [views, setViews] = useState(null);
  const [loading, setLoading] = useState(true);

  const mainRef = useRef(null);
  const itemLatestRef = useRef(null);
  const itemRelRef = useRef(null);
  const [latestCount, setLatestCount] = useState(5);
  const [relatedCount, setRelatedCount] = useState(5);

  const inflightRef = useRef(false);
  const hasRedirectedRef = useRef(false);
  const lastRunAtRef = useRef(0);

  // ---------- основная загрузка ----------
  useEffect(() => {
    let cancelled = false;

    async function load() {
      // анти-дребезг
      const now = Date.now();
      if (inflightRef.current || now - lastRunAtRef.current < 600) return;
      lastRunAtRef.current = now;

      // глобальный кэш — если уже грузили этот путь, не повторяем
      const loaded = getLoadedSet();
      const cacheKey = location.pathname; // учитываем полный путь
      if (loaded.has(cacheKey)) {
        setLoading(false);
        return;
      }

      inflightRef.current = true;
      setLoading(true);

      try {
        window.scrollTo({ top: 0, behavior: "instant" });

        let finalType = null;
        let finalParam = null;
        let finalSlug = slug;

        // 1) сначала пытаемся определить тип из URL, без resolve
        if (source && slug) {
          finalType = "rss";
          finalParam = source;
          finalSlug = slug;
        } else if (category && slug) {
          finalType = "article";
          finalParam = category;
          finalSlug = slug;
        } else {
          // 2) «короткая» ссылка — используем resolve
          try {
            const r = await resolveNews(slug);

            const current = window.location.pathname.replace(/\/+$/, "");
            const target = r?.seo_url?.replace(/\/+$/, "");
            if (target && current !== target && !hasRedirectedRef.current) {
              hasRedirectedRef.current = true;
              navigate(target, { replace: true });
              return; // дальше не продолжаем — будет новый mount
            }

            finalType = r?.type || null;
            finalSlug = r?.slug || slug;
            if (finalType === "rss") finalParam = r?.source;
            else if (finalType === "article") finalParam = r?.category || "news";
          } catch (e) {
            console.warn("resolveNews не дал ответа, попробуем прямые ручки:", e);
          }
        }

        // 3) тянем новость
        let item = null;
        try {
          if (finalType === "article" && finalParam && finalSlug) {
            item = await fetchArticle(finalParam, finalSlug);
          } else if (finalType === "rss" && finalParam && finalSlug) {
            item = await fetchImportedNews(finalParam, finalSlug);
          } else {
            // в крайнем случае пробуем оба по очереди (но БЕЗ resolve)
            try { item = await fetchImportedNews(source || "source", finalSlug); } catch {}
            if (!item) try { item = await fetchArticle(category || "news", finalSlug); } catch {}
          }
        } catch (err) {
          console.error("Ошибка загрузки новости:", err);
        }

        // 4) поправляем URL, если есть расхождение
        if (item?.slug) {
          const seoUrl = item?.source
            ? `/news/source/${item.source?.slug || "source"}/${item.slug}`
            : `/news/${item.categories?.[0]?.slug || "news"}/${item.slug}`;
          const current = window.location.pathname.replace(/\/+$/, "");
          if (seoUrl.replace(/\/+$/, "") !== current && !hasRedirectedRef.current) {
            hasRedirectedRef.current = true;
            navigate(seoUrl, { replace: true });
            return;
          }
        }

        if (!cancelled) setNews(item || null);

        // 5) похожие
        if (!cancelled && item?.slug) {
          try {
            const typeGuess = item?.source ? "rss" : "article";
            const paramGuess = item?.source?.slug || item?.categories?.[0]?.slug || "news";
            const rel = await fetchRelated(typeGuess, paramGuess, item.slug);
            if (!cancelled) setRelated(rel || []);
          } catch (e) {
            console.warn("fetchRelated error:", e);
          }
        }

        // 6) метрики
        if (!cancelled && item?.slug) {
          try {
            const typeGuess = item?.source ? "rss" : "article";
            const d = await hitMetrics(typeGuess, item.slug);
            if (!cancelled && d?.views) setViews(d.views);
          } catch (e) {
            console.warn("hitMetrics error:", e);
          }
        }

        // помечаем путь как загруженный
        loaded.add(cacheKey);
      } finally {
        inflightRef.current = false;
        if (!cancelled) setLoading(false);
      }
    }

    hasRedirectedRef.current = false; // один редирект на slug
    load();

    return () => { cancelled = true; };
    // ВАЖНО: завязываемся на ПОЛНЫЙ путь. Если родитель нас «перемонтирует» с тем же slug,
    // но иным path (например, хвосты/слэши), это будет считаться новым кейсом — и ок.
  }, [slug, source, category, location.pathname, navigate]);

  // ---------- последние новости ----------
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetchNews();
        if (cancelled) return;
        const data = Array.isArray(res) ? res : res?.results || [];
        setLatest(data);
      } catch (e) {
        console.warn("fetchNews error:", e);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // ---------- автоподгонка ----------
  useEffect(() => {
    function adjustHeights() {
      if (!mainRef.current) return;
      const mainHeight = mainRef.current.offsetHeight;
      if (itemLatestRef.current) {
        const h = itemLatestRef.current.offsetHeight;
        if (h > 0) setLatestCount(Math.max(1, Math.floor(mainHeight / h)));
      }
      if (itemRelRef.current) {
        const h = itemRelRef.current.offsetHeight;
        if (h > 0) setRelatedCount(Math.max(1, Math.floor(mainHeight / h)));
      }
    }
    adjustHeights();
    window.addEventListener("resize", adjustHeights);
    return () => window.removeEventListener("resize", adjustHeights);
  }, [loading, latest, related]);

  // ---------- рендер ----------
  if (loading)
    return (
      <div className={s.pageWrap}>
        <div className={s.main}>Загрузка…</div>
      </div>
    );

  if (!news)
    return (
      <div className={s.pageWrap}>
        <div className={s.main}>Новость не найдена.</div>
      </div>
    );

  const categoryName = news?.categories?.[0]?.name || news?.source?.name || "Новости";

  return (
    <div className={s.pageWrap}>
      <aside className={s.leftAside}>
        <div className={s.sectionH}>Последние новости</div>
        <div className={s.latestList}>
          {latest.slice(0, latestCount).map((n, i) => (
            <Link
              key={n.slug}
              to={
                n.source
                  ? `/news/source/${n.source.slug}/${n.slug}`
                  : `/news/${n.category?.slug || n.categories?.[0]?.slug || "news"}/${n.slug}`
              }
              ref={i === 0 ? itemLatestRef : null}
              className={s.latestItem}
            >
              {n.title}
            </Link>
          ))}
        </div>
      </aside>

      <article className={s.main} ref={mainRef}>
        <div className={s.breadcrumbs}>
          <Link to="/" className={s.breadcrumbLink}>Главная</Link>
          <span className={s.breadcrumbSep}>›</span>
          {news.source ? (
            <Link to={`/news/source/${news.source.slug}`} className={s.breadcrumbLink}>
              {news.source.name}
            </Link>
          ) : (
            <Link to={`/category/${news.categories?.[0]?.slug || "news"}`} className={s.breadcrumbLink}>
              {categoryName}
            </Link>
          )}
          <span className={s.breadcrumbSep}>›</span>
          <span className={s.breadcrumbCurrent}>{news.title}</span>
        </div>

        <h1 className={s.title}>{news.title}</h1>
        <div className={s.meta}>
          {sourceDisplay(news)} •{" "}
          {news.published_at && new Date(news.published_at).toLocaleString()} •{" "}
          {views || 0} просмотров
        </div>

        {(news.cover_image || news.image) && (
          <img
            src={news.cover_image || news.image || "/static/img/default_news.svg"}
            alt={news.title}
            className={s.cover}
          />
        )}

        <div
          className={s.body}
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(news.content || news.summary || "") }}
        />

        {news.link && (
          <div className={s.external}>
            <a href={news.link} target="_blank" rel="noopener noreferrer" className={s.externalLink}>
              Читать в источнике →
            </a>
          </div>
        )}
      </article>

      <aside className={s.rightAside}>
        <div className={s.sectionH}>Похожие новости</div>
        {related.slice(0, relatedCount).map((n, i) => (
          <Link
            key={n.slug}
            to={
              n.source
                ? `/news/source/${n.source.slug}/${n.slug}`
                : `/news/${n.category?.slug || n.categories?.[0]?.slug || "news"}/${n.slug}`
            }
            ref={i === 0 ? itemRelRef : null}
            className={s.relItem}
          >
            <img
              src={n.image || n.cover_image || "/static/img/default_news.svg"}
              alt=""
              className={s.relThumb}
            />
            <div>
              <div className={s.relTitle}>{n.title}</div>
              <div className={s.relSource}>{sourceDisplay(n)}</div>
            </div>
          </Link>
        ))}
      </aside>
    </div>
  );
}
