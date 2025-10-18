/* Путь: frontend/src/pages/NewsDetailPage.js
   Назначение: Детальная страница новости (Article или ImportedNews).

   В этой версии:
   ✅ «Похожие» никогда не содержат текущую открытую новость:
      - новая функция filterOutCurrent(list, curSlug, curId)
      - фильтрация применяется при setRelated/setCachedRelated и дополнительно при подготовке к рендеру
   ✅ Сохранены: мгновенный сброс правой колонки при смене slug, гарды от устаревших ответов,
      быстрый parallel race + кеш (in-memory + sessionStorage), скелетоны и fade-in анимации,
      pretty <title>, SmartTitle/ArticleBody/SmartMedia, синхронизация высот.
*/

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import DOMPurify from "dompurify";
import s from "./NewsDetailPage.module.css";
import sk from "./NewsDetailPageSkeleton.module.css";
import anim from "./NewsDetailPageAnim.module.css";

import { fetchRelated, fetchArticle, fetchNews, hitMetrics, fetchCategories } from "../Api";
import SmartMedia from "../components/SmartMedia";
import ArticleBody from "../components/ArticleBody";
import SmartTitle from "../components/SmartTitle";
import { buildPrettyTitle } from "../utils/title";

// ================= УТИЛИТЫ API и КАРТИНКИ =================
const API_BASE = "http://localhost:8000/api";
const BACKEND_ORIGIN = "http://localhost:8000";

/** Универсальный GET JSON */
async function getJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) return null;
  return await resp.json();
}

/** Абсолютный URL для /media/... */
function absoluteMedia(urlOrPath) {
  if (!urlOrPath) return null;
  try {
    const u = new URL(urlOrPath);
    return u.href;
  } catch {
    const path = urlOrPath.startsWith("/") ? urlOrPath : `/${urlOrPath}`;
    return `${BACKEND_ORIGIN}${path}`;
  }
}

/** /api/media/thumbnail/?src=... */
function buildThumb(src, { w = 640, h = 360, fit = "cover", fmt = "webp", q = 82 } = {}) {
  if (!src) return null;
  const params = new URLSearchParams({ src, w: String(w), h: String(h), fit, fmt, q: String(q) });
  return `${API_BASE}/media/thumbnail/?${params.toString()}`;
}

/** Нормализуем карточку похожих (картинки -> абсолютные, создаём превью) */
function normalizeRelated(items) {
  if (!Array.isArray(items)) return [];
  return items.map((it) => {
    const imageAbs = it.image ? absoluteMedia(it.image) : null;
    const thumb = imageAbs ? buildThumb(imageAbs, { w: 640, h: 360, fit: "cover", fmt: "webp", q: 82 }) : null;
    return { ...it, imageAbs, thumb };
  });
}

/** Fallback: список новостей категории — сначала новый /api/news/<slug>/, затем старый /api/category/<slug>/ */
async function fetchCategoryLatest(catSlug, limit = 8) {
  try {
    const d1 = await getJson(`${API_BASE}/news/${encodeURIComponent(catSlug)}/?limit=${limit}`);
    const arr1 = Array.isArray(d1?.results) ? d1.results : Array.isArray(d1) ? d1 : [];
    const n1 = normalizeRelated(arr1).slice(0, limit);
    if (n1.length) return n1;
  } catch {}
  try {
    const d2 = await getJson(`${API_BASE}/category/${encodeURIComponent(catSlug)}/`);
    const arr2 = Array.isArray(d2?.results) ? d2.results : Array.isArray(d2) ? d2 : [];
    return normalizeRelated(arr2).slice(0, limit);
  } catch {
    return [];
  }
}

/** Fallback: детальная новость по универсальному роуту /api/news/<slug>/ */
async function fetchArticleUniversal(slug) {
  if (!slug) return null;
  try {
    return await getJson(`${API_BASE}/news/${encodeURIComponent(slug)}/`);
  } catch {
    return null;
  }
}

/** СТАРАЯ ПОСЛЕДОВАТЕЛЬНАЯ ВЕРСИЯ — оставлена для совместимости (подавлен eslint) */
// eslint-disable-next-line no-unused-vars
async function fetchRelatedVariants(slug, categorySlug, limit = 8) {
  if (!slug) return [];
  let items = null;

  try {
    const d = await getJson(`${API_BASE}/news/${encodeURIComponent(slug)}/related/?limit=${limit}`);
    items = normalizeRelated(d?.items || d || []);
    if (items.length) return items;
  } catch {}

  try {
    const d = await getJson(`${API_BASE}/news/related/${encodeURIComponent(slug)}/?limit=${limit}`);
    items = normalizeRelated(d?.items || d || []);
    if (items.length) return items;
  } catch {}

  try {
    const legacy = await fetchRelated("article", categorySlug || "news", slug);
    items = normalizeRelated(legacy || []);
    if (items.length) return items;
  } catch {}

  try {
    items = await fetchCategoryLatest(categorySlug || "news", limit);
    if (items.length) return items;
  } catch {}

  return [];
}

/* ==================== БЫСТРАЯ ПАРАЛЛЕЛЬНАЯ ВЫДАЧА (RACE + TIMEOUTS) ==================== */
function withTimeout(promise, ms = 1200) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), ms)),
  ]);
}

async function fetchJsonArray(url, timeoutMs = 1200) {
  try {
    const d = await withTimeout(getJson(url), timeoutMs);
    const arr =
      Array.isArray(d?.items) ? d.items :
      Array.isArray(d?.results) ? d.results :
      Array.isArray(d) ? d : [];
    return normalizeRelated(arr);
  } catch {
    return [];
  }
}

/** Параллельный сбор с «первым непустым» + запасной по категории */
async function fetchRelatedVariantsFast(slug, categorySlug, limit = 8) {
  if (!slug) return [];

  const p1 = fetchJsonArray(`${API_BASE}/news/${encodeURIComponent(slug)}/related/?limit=${limit}`, 1200);
  const p2 = fetchJsonArray(`${API_BASE}/news/related/${encodeURIComponent(slug)}/?limit=${limit}`, 1200);
  const p3 = (async () => {
    try {
      const legacy = await withTimeout(
        (async () => normalizeRelated(await fetchRelated("article", categorySlug || "news", slug) || []))(),
        1500
      );
      return legacy;
    } catch {
      return [];
    }
  })();
  const p4 = fetchCategoryLatest(categorySlug || "news", limit);

  try {
    const first = await Promise.any([
      p1.then(a => (a && a.length ? a : Promise.reject())),
      p2.then(a => (a && a.length ? a : Promise.reject())),
      p3.then(a => (a && a.length ? a : Promise.reject())),
      p4.then(a => (a && a.length ? a : Promise.reject())),
    ]);
    return first.slice(0, limit);
  } catch {
    const [a1, a2, a3, a4] = await Promise.all([p1, p2, p3, p4]);
    const best = [a1, a2, a3, a4].find(a => a && a.length) || [];
    return best.slice(0, limit);
  }
}

/* ================= КЕШ «ПОХОЖИХ» (память вкладки + sessionStorage) ================= */
const RELATED_CACHE_TTL = 5 * 60 * 1000; // 5 минут
const relatedCache = new Map(); // key: slug → { ts, items }

function ssGet(slug) {
  try {
    const raw = sessionStorage.getItem(`related:${slug}`);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    if (!obj?.ts || !Array.isArray(obj.items)) return null;
    if (Date.now() - obj.ts > RELATED_CACHE_TTL) return null;
    return obj.items;
  } catch {
    return null;
  }
}
function ssSet(slug, items) {
  try {
    sessionStorage.setItem(`related:${slug}`, JSON.stringify({ ts: Date.now(), items }));
  } catch {}
}

function getCachedRelated(slug) {
  const mem = relatedCache.get(slug);
  if (mem && Date.now() - mem.ts <= RELATED_CACHE_TTL) return mem.items;
  const ss = ssGet(slug);
  return ss || null;
}
function setCachedRelated(slug, items) {
  relatedCache.set(slug, { ts: Date.now(), items });
  ssSet(slug, items);
}

function formatRuPortalDate(isoString, tz = "Europe/Moscow") {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    if (Number.isNaN(d.getTime())) return String(isoString);
    const fmt = new Intl.DateTimeFormat("ru-RU", {
      timeZone: tz,
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    const parts = {};
    for (const p of fmt.formatToParts(d)) {
      if (p.type !== "literal") parts[p.type] = p.value;
    }
    return `${parts.day} ${parts.month} ${parts.year}, ${parts.hour}:${parts.minute}`;
  } catch {
    return String(isoString);
  }
}

function isLikelyISO(v) {
  if (!v) return false;
  const s = String(v).trim();
  return /^\d{4}-\d{2}-\d{2}T/.test(s) || /^\d{4}-\d{2}-\d{2}\s/.test(s);
}

// очеловечивание slug
function humanizeSlug(slug) {
  if (!slug) return "";
  const map = {
    "bez-kategorii": "Без категории",
    "lenta-novostej": "Лента новостей",
    "v-mire": "В мире",
    "v-rossii": "В России",
    "armija-i-opk": "Армия и ОПК",
    "byvshij-sssr": "Бывший СССР",
    "silovye-struktury": "Силовые структуры",
    "nauka-i-tehnika": "Наука и техника",
  };
  if (map[slug]) return map[slug];
  return slug
    .split("-")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : ""))
    .join(" ");
}

/* ================= ВСПОМОГАТЕЛЬНОЕ: определение slug и фильтрация текущей новости ================= */
function extractSlug(maybeUrl) {
  if (!maybeUrl) return "";
  try {
    // поддержка относительных путей и абсолютных URL
    const u = new URL(maybeUrl, BACKEND_ORIGIN);
    const parts = u.pathname.replace(/\/+$/, "").split("/").filter(Boolean);
    return parts[parts.length - 1] || "";
  } catch {
    // на случай, если пришло не-URL, попробуем как строку пути
    const parts = String(maybeUrl).replace(/\/+$/, "").split("/").filter(Boolean);
    return parts[parts.length - 1] || "";
  }
}

/** Удаляем из списка элемент, соответствующий текущей открытой новости */
function filterOutCurrent(list, curSlug, curId) {
  const curSlugLC = (curSlug || "").toLowerCase();
  const curIdStr = curId != null ? String(curId) : null;

  return (Array.isArray(list) ? list : []).filter((n) => {
    const nid = n?.id ?? n?.pk ?? null;
    if (curIdStr && nid != null && String(nid) === curIdStr) return false;

    const nSlug =
      (n?.slug || n?.news_slug || extractSlug(n?.seo_url) || "").toLowerCase();

    if (curSlugLC && nSlug && nSlug === curSlugLC) return false;
    return true;
  });
}

export default function NewsDetailPage() {
  const params = useParams();
  const [item, setItem] = useState(null);

  const [latest, setLatest] = useState([]);
  const [latestLoading, setLatestLoading] = useState(true); // скелетоны слева

  const [related, setRelated] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(true); // скелетоны справа

  const [error, setError] = useState(null);
  const [catDict, setCatDict] = useState({});

  const leftRef = useRef(null);
  const mainRef = useRef(null);
  const rightRef = useRef(null);

  /** Актуальный slug, чтобы игнорировать устаревшие ответы */
  const latestSlugRef = useRef(null);

  // ====== ПОДГОТОВКА: сначала убираем текущую новость из «related», потом сортируем ======
  const relatedFiltered = useMemo(() => {
    const curSlug = item?.slug || params?.slug || "";
    const curId = item?.id ?? item?.pk ?? null;
    return filterOutCurrent(related, curSlug, curId);
  }, [related, item?.slug, item?.id, item?.pk, params?.slug]);

  const preparedRelated = useMemo(() => {
    return (relatedFiltered || []).map((n, idx) => {
      const img = n?.thumb || n?.imageAbs || (n?.image ? absoluteMedia(n.image) : null);
      return { ...n, __img: img, __hasImg: Boolean(img), __idx: idx };
    });
  }, [relatedFiltered]);

  const sortedRelated = useMemo(() => {
    const withImg = [];
    const withoutImg = [];
    for (const it of preparedRelated) (it.__hasImg ? withImg : withoutImg).push(it);
    withImg.sort((a, b) => a.__idx - b.__idx);
    withoutImg.sort((a, b) => a.__idx - b.__idx);
    return withImg.concat(withoutImg);
  }, [preparedRelated]);

  // Категории для хлебных крошек
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const cats = await fetchCategories();
        if (!cancelled && Array.isArray(cats)) {
          const dict = {};
          for (const c of cats) dict[c.slug] = c.name || c.title || humanizeSlug(c.slug);
          setCatDict(dict);
        }
      } catch {}
    })();
    return () => { cancelled = true; };
  }, []);

  // Preconnect/dns-prefetch к бэку
  useEffect(() => {
    const preconnect = document.createElement("link");
    preconnect.rel = "preconnect";
    preconnect.href = BACKEND_ORIGIN;
    preconnect.crossOrigin = "";
    const dns = document.createElement("link");
    dns.rel = "dns-prefetch";
    dns.href = BACKEND_ORIGIN;
    document.head.append(preconnect, dns);
    return () => {
      try { document.head.removeChild(preconnect); } catch {}
      try { document.head.removeChild(dns); } catch {}
    };
  }, []);

  /* ========== РЕСЕТ И РАННИЙ СТАРТ «ПОХОЖИХ» ДЛЯ ТЕКУЩЕГО SLUG (с фильтрацией текущей новости) ========== */
  useEffect(() => {
    let cancelled = false;
    const slug = params?.slug;
    const categoryParam = params?.category || "news";
    if (!slug) return;

    latestSlugRef.current = slug;
    setRelated([]);           // мгновенный сброс
    setRelatedLoading(true);  // включаем скелетоны

    // Prefetch related-эндпоинта
    try {
      const pre = document.createElement("link");
      pre.rel = "prefetch";
      pre.href = `${API_BASE}/news/${encodeURIComponent(slug)}/related/?limit=8`;
      document.head.appendChild(pre);
      setTimeout(() => { try { document.head.removeChild(pre); } catch {} }, 5000);
    } catch {}

    // 1) кеш
    const cachedRaw = getCachedRelated(slug);
    const cached = filterOutCurrent(cachedRaw || [], slug, null);
    if (cached && cached.length) {
      if (latestSlugRef.current === slug && !cancelled) {
        setRelated(cached);
        setRelatedLoading(false);
      }
    }

    // 2) быстрый запасной по категории
    (async () => {
      try {
        if (!cached || cached.length === 0) {
          const catFastRaw = await fetchCategoryLatest(categoryParam, 8);
          const catFast = filterOutCurrent(catFastRaw, slug, null);
          if (!cancelled && latestSlugRef.current === slug && catFast.length) {
            setRelated(catFast);
            setRelatedLoading(false);
          }
        }
      } catch {}
    })();

    // 3) основной быстрый сбор (race + timeouts)
    (async () => {
      try {
        const listRaw = await fetchRelatedVariantsFast(slug, categoryParam, 8);
        const list = filterOutCurrent(listRaw, slug, null);
        if (cancelled || latestSlugRef.current !== slug) return;
        setCachedRelated(slug, list);
        setRelated(list);
      } finally {
        if (!cancelled && latestSlugRef.current === slug) setRelatedLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [params?.slug, params?.category]);

  // Основная загрузка: статья + последние (слева)
  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const slug = params?.slug;
        const categoryParam = params?.category || "news";
        if (!slug) throw new Error("slug не найден в параметрах");

        let article = null;
        try { article = await fetchArticle(categoryParam, slug); } catch {}
        if (!article) { try { article = await fetchArticleUniversal(slug); } catch {} }

        if (!article) {
          article = { title: "Новость не найдена", category: { slug: categoryParam, title: categoryParam }, content: "" };
        }
        if (cancelled) return;
        setItem(article);

        setLatestLoading(true);
        try {
          const lastRes = await fetchNews(1);
          if (!cancelled) setLatest(lastRes || []);
        } catch {}
        if (!cancelled) setLatestLoading(false);

        const slugForMetrics = article.slug || slug;
        if (slugForMetrics) hitMetrics("article", slugForMetrics).catch(() => {});
      } catch (e) {
        console.error(e);
        if (!cancelled) setError(e?.message || "Ошибка загрузки новости");
      }
    }

    load();
    return () => { cancelled = true; };
  }, [params?.slug, params?.category]);

  // <title>
  useEffect(() => {
    if (!item?.title) return;
    const prev = document.title;
    document.title = buildPrettyTitle(item.title);
    return () => { document.title = prev; };
  }, [item?.title]);

  // Синхронизация высот колонок
  useEffect(() => {
    if (!mainRef.current || !leftRef.current || !rightRef.current) return;
    const syncHeights = () => {
      const isMobile = window.matchMedia("(max-width: 960px)").matches;
      if (isMobile) {
        if (leftRef.current) leftRef.current.style.height = "auto";
        if (rightRef.current) rightRef.current.style.height = "auto";
        return;
      }
      const h = mainRef.current ? mainRef.current.offsetHeight || 0 : 0;
      if (leftRef.current) leftRef.current.style.height = `${h}px`;
      if (rightRef.current) rightRef.current.style.height = `${h}px`;
    };
    const ro = new ResizeObserver(syncHeights);
    ro.observe(mainRef.current);
    window.addEventListener("resize", syncHeights);
    syncHeights();
    return () => { try { ro.disconnect(); } catch {}; window.removeEventListener("resize", syncHeights); };
  }, [item, latest, related, latestLoading, relatedLoading]);

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

  const imageRaw = item.image || item.cover_image || item.cover || item.image_url || null;
  const sourceTitle = item.source_title || item.source || "";
  const externalUrl = item.original_url || item.link || item.url || null;

  const contentHtml = DOMPurify.sanitize(item.content || item.summary || "", { USE_PROFILES: { html: true } });

  const sourceLogo =
    item.source_logo ||
    item.source_logo_url ||
    (item.source_fk && (item.source_fk.logo || item.source_fk.icon)) ||
    (item.source && item.source.logo) ||
    "";

  const dateCandidate =
    (isLikelyISO(item.pub_date_fmt) && item.pub_date_fmt) ||
    item.published_at || item.date || item.created_at || item.updated_at || item.pub_date_fmt || "";
  const datePretty = formatRuPortalDate(dateCandidate, "Europe/Moscow");

  const categorySlug = item.category?.slug || params?.category || "news";
  const categoryTitle =
    item.category?.name || item.category?.title || catDict[categorySlug] || humanizeSlug(categorySlug);

  return (
    <div className={`news-detail ${s.pageWrap}`}>
      <aside className={s.leftAside} ref={leftRef}>
        <div className={s.sectionH}>Последние новости</div>

        {latestLoading && latest.length === 0 ? (
          <div className={sk.skelLatestCol} role="status" aria-label="Загрузка последних">
            {Array.from({ length: 7 }).map((_, i) => (
              <div className={sk.skelLatestLine} key={`lt-skel-${i}`} />
            ))}
          </div>
        ) : (
          <div className={`${s.latestList} ${anim.fadeIn}`}>
            {latest.map((n) => (
              <Link
                key={`l-${n.id || n.slug}`}
                to={n.seo_url || `/${n.category?.slug ?? "news"}/${n.slug ?? ""}/`}
                className={s.latestItem}
              >
                {buildPrettyTitle(n.title || "")}
              </Link>
            ))}
          </div>
        )}
      </aside>

      <main className={s.main} ref={mainRef}>
        <SmartTitle item={item} as="h1" className={s.title} />

        <div className={s.breadcrumbs}>
          <Link to="/">Главная</Link>
          <span className={s.breadcrumbSeparator}>›</span>
          <Link to={`/${categorySlug}/`}>{categoryTitle}</Link>
        </div>

        <div className={s.meta}>
          {datePretty}
          {sourceTitle ? " • " + sourceTitle : ""}
        </div>

        {imageRaw ? (
          <SmartMedia
            src={imageRaw}
            alt={item.title || ""}
            title={item.title || ""}
            sourceLogo={sourceLogo}
            className={s.cover}
          />
        ) : null}

        {(item.summary || item.content) && (
          <ArticleBody html={contentHtml} baseUrl={externalUrl || ""} className={s.body} />
        )}

        {externalUrl && (
          <div className={s.external}>
            <a className={s.externalLink} href={externalUrl} target="_blank" rel="noreferrer">
              Читать в источнике →
            </a>
          </div>
        )}
      </main>

      <aside className={s.rightAside} ref={rightRef}>
        <div className={s.sectionH}>Похожие новости</div>

        {relatedLoading && sortedRelated.length === 0 ? (
          <div className={sk.skelGrid} role="status" aria-label="Загрузка похожих">
            {Array.from({ length: 6 }).map((_, i) => (
              <div className={sk.skelRelItem} key={`rl-skel-${i}`}>
                <div className={sk.skelThumb} />
                <div className={sk.skelLines}>
                  <div className={sk.skelLine} />
                  <div className={sk.skelLineShort} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={`${s.relList} ${anim.fadeIn}`}>
            {sortedRelated.map((n) => {
              const hasImg = n.__hasImg;
              const img = n.__img;
              return (
                <Link
                  key={`r-${n.id || n.slug || n.__idx}`}
                  to={n.seo_url || `/${n.category?.slug ?? "news"}/${n.slug ?? ""}/`}
                  className={s.relItem}
                  style={
                    hasImg
                      ? { display: "grid", gridTemplateColumns: "84px 1fr", gap: 12, alignItems: "center" }
                      : { display: "block" }
                  }
                >
                  {hasImg ? (
                    <img
                      className={s.relThumb}
                      src={img}
                      alt=""
                      loading="lazy"
                      width={84}
                      height={84}
                      style={{ width: 84, height: 84, objectFit: "cover", borderRadius: 8 }}
                    />
                  ) : null}

                  <div style={{ width: "100%" }}>
                    <div className={s.relTitle}>{buildPrettyTitle(n.title || "")}</div>
                    <div className={s.relSource}>{n.source_title || n.source || ""}</div>
                  </div>
                </Link>
              );
            })}
            {!relatedLoading && sortedRelated.length === 0 && (
              <div className={s.relEmpty}>Нет похожих материалов.</div>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
