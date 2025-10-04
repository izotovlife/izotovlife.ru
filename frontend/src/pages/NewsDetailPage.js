// Путь: frontend/src/pages/NewsDetailPage.js
// Назначение: Детальная страница новости (Article или Imported RSS).
// Особенности:
//   ✅ Сначала делает resolve(slug), чтобы определить тип и SEO-URL.
//   ✅ Защищён от циклов navigate().
//   ✅ Безопасно вызывает fetchRelated и hitMetrics.

import React, { useEffect, useState, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
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

// ---------------- Утилиты ----------------
function getHostname(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}
function sourceDisplay(n) {
  return (
    n?.source?.name || n?.source_name || getHostname(n?.link || "") || "Источник"
  );
}

// ---------------- Компонент ----------------
export default function NewsDetailPage() {
  const { category, source, slug } = useParams();
  const navigate = useNavigate();

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

  // 🔒 Флаги
  const didInitRef = useRef(false);
  const inflightRef = useRef(false);
  const lastSlugRef = useRef(null);
  const hasRedirectedRef = useRef(false);

  // ---------------- Загрузка новости ----------------
  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (inflightRef.current && lastSlugRef.current === slug) return;
      inflightRef.current = true;
      lastSlugRef.current = slug;

      try {
        setLoading(true);
        window.scrollTo({ top: 0, behavior: "instant" });

        let finalType = null;
        let finalParam = null;
        let finalSlug = slug;

        // 1️⃣ Резолвим slug → тип, seo_url
        try {
          const r = await resolveNews(slug);

          // очищаем URLы (без / и без origin)
          const current = window.location.pathname.replace(/\/+$/, "");
          const target = r?.seo_url?.replace(/\/+$/, "");
          if (
            target &&
            current !== target &&
            !hasRedirectedRef.current // 🚫 второй раз не редиректим
          ) {
            console.log("➡️ redirect to SEO URL:", target);
            hasRedirectedRef.current = true;
            navigate(target, { replace: true });
            inflightRef.current = false;
            return;
          }

          finalType = r?.type || null;
          finalSlug = r?.slug || slug;
          if (finalType === "rss") finalParam = r?.source;
          else if (finalType === "article")
            finalParam = r?.category || category || "news";
        } catch (e) {
          if (source && slug) {
            finalType = "rss";
            finalParam = source;
            finalSlug = slug;
          } else if (category && slug) {
            finalType = "article";
            finalParam = category;
            finalSlug = slug;
          } else {
            console.warn("resolveNews: не найден:", e);
          }
        }

        // 2️⃣ Загружаем саму новость
        let item = null;
        try {
          if (finalType === "article") {
            item = await fetchArticle(finalParam, finalSlug);
          } else if (finalType === "rss") {
            item = await fetchImportedNews(finalParam, finalSlug);
          }
        } catch (err) {
          console.error("Ошибка загрузки новости:", err);
        }

        // 3️⃣ Проверяем URL — если отличается
        if (item?.slug) {
          const seoUrl = item?.source
            ? `/news/source/${item.source?.slug || "source"}/${item.slug}`
            : `/news/${item.categories?.[0]?.slug || "news"}/${item.slug}`;
          const current = window.location.pathname.replace(/\/+$/, "");
          if (
            seoUrl.replace(/\/+$/, "") !== current &&
            !hasRedirectedRef.current
          ) {
            console.log("➡️ redirect to item slug:", seoUrl);
            hasRedirectedRef.current = true;
            navigate(seoUrl, { replace: true });
            inflightRef.current = false;
            return;
          }
        }

        if (!cancelled) setNews(item || null);

        // 4️⃣ Похожие
        if (finalType && finalParam && finalSlug) {
          try {
            const rel = await fetchRelated(finalType, finalParam, finalSlug);
            if (!cancelled) setRelated(rel || []);
          } catch (e) {
            console.warn("fetchRelated error:", e);
          }
        }

        // 5️⃣ Метрики
        if (item?.slug && finalType) {
          try {
            const d = await hitMetrics(finalType, item.slug);
            if (!cancelled && d?.views) setViews(d.views);
          } catch (e) {
            console.warn("hitMetrics error:", e);
          }
        }
      } catch (e) {
        console.error("Ошибка загрузки:", e);
        if (!cancelled) {
          setNews(null);
          setRelated([]);
        }
      } finally {
        inflightRef.current = false;
        if (!cancelled) setLoading(false);
      }
    }

    // StrictMode защита
    if (!didInitRef.current) {
      didInitRef.current = true;
      load();
    } else {
      load();
    }

    return () => {
      cancelled = true;
    };
  }, [slug, category, source, navigate]);

  // ---------------- Последние новости ----------------
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
    return () => {
      cancelled = true;
    };
  }, []);

  // ---------------- Автоподгонка ----------------
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

  // ---------------- Рендер ----------------
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

  const categoryName =
    news?.categories?.[0]?.name || news?.source?.name || "Новости";

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
          <Link to="/" className={s.breadcrumbLink}>
            Главная
          </Link>
          <span className={s.breadcrumbSep}>›</span>
          {news.source ? (
            <Link
              to={`/news/source/${news.source.slug}`}
              className={s.breadcrumbLink}
            >
              {news.source.name}
            </Link>
          ) : (
            <Link
              to={`/category/${news.categories?.[0]?.slug || "news"}`}
              className={s.breadcrumbLink}
            >
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

        {news.cover_image && (
          <img src={news.cover_image} alt="" className={s.cover} />
        )}

        <div
          className={s.body}
          dangerouslySetInnerHTML={{
            __html: DOMPurify.sanitize(news.content || news.summary || ""),
          }}
        />

        {news.link && (
          <div className={s.external}>
            <a
              href={news.link}
              target="_blank"
              rel="noopener noreferrer"
              className={s.externalLink}
            >
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
              src={n.image || "/static/img/default_news.svg"}
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
