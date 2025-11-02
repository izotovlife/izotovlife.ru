// Путь: frontend/src/pages/NewsDetailPage.js
// Назначение: Детальная страница новости (Article или ImportedNews).
//
// Обновлено (ничего полезного не удалял, только усилил совместимость и скорость):
//   ✅ Исправлен путь related: сначала /news/related/<slug>/ (совпадает с backend/urls.py), потом /news/<slug>/related/
//   ✅ В related-запросы добавлен fields=id,slug,title,thumbnail,category_slug,category_name,published_at,seo_url
//   ✅ Ленивая загрузка «Похожих» теперь безопасная: по умолчанию грузим сразу (relCanLoad=true),
//      IntersectionObserver — только как дополнительный триггер, не блокирует загрузку
//   ✅ AbortController для related-запросов (гонки прерываются)
//   ✅ Подушка категории через Api.fetchCategoryNews() — никаких 404
//   ✅ Обложка без заглушек: если битая — просто скрываем

import React, { useEffect, useMemo, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import DOMPurify from "dompurify";
import s from "./NewsDetailPage.module.css";
import sk from "./NewsDetailPageSkeleton.module.css";
import anim from "./NewsDetailPageAnim.module.css";

import {
  fetchRelated,
  fetchArticle,
  fetchNews,
  hitMetrics,
  fetchCategories,
  fetchCategoryNews,              // «подушка» категории
  API_BASE as API_BASE_FROM_API,
  buildThumb as buildThumbFromApi,
} from "../Api";
// SmartMedia убран намеренно — обложку показываем только если есть валидное фото (без плейсхолдеров)
import ArticleBody from "../components/ArticleBody";
import SmartTitle from "../components/SmartTitle";
import { buildPrettyTitle } from "../utils/title";
import { FiExternalLink, FiClock, FiLink } from "react-icons/fi";
import { FaVk, FaTelegramPlane, FaWhatsapp, FaOdnoklassniki } from "react-icons/fa";
import FavoriteHeart from "../components/FavoriteHeart";

// ================= НАСТРОЙКИ API (с фолбэком) =================
const API_BASE = (API_BASE_FROM_API || "http://127.0.0.1:8000/api").replace(/\/$/, "");
let BACKEND_ORIGIN = "http://127.0.0.1:8000";
try {
  BACKEND_ORIGIN = new URL(API_BASE).origin;
} catch {}

const RELATED_FIELDS =
  "id,slug,title,thumbnail,category_slug,category_name,published_at,seo_url,image,category";

// ================= УТИЛИТЫ FETCH/URL/THUMB =================
async function getJson(url, opts = {}) {
  try {
    const resp = await fetch(url, { credentials: "include", signal: opts.signal });
    if (!resp.ok) return null;
    const text = await resp.text();
    if (!text) return null;
    try { return JSON.parse(text); } catch { return null; }
  } catch { return null; }
}
function isHttpLike(u) {
  try { return /^https?:\/\//i.test(String(u)); } catch { return false; }
}
function isDataOrBlob(u) {
  try { return /^(data:|blob:|about:)/i.test(String(u)); } catch { return false; }
}
function absoluteMedia(urlOrPath) {
  if (!urlOrPath) return null;
  try { if (isHttpLike(urlOrPath)) return new URL(urlOrPath).href; } catch {}
  const p = String(urlOrPath).startsWith("/") ? String(urlOrPath) : `/${String(urlOrPath)}`;
  return `${BACKEND_ORIGIN}${p}`;
}
function buildThumb(src, { w = 640, h = 360, fit = "cover", fmt = "webp", q = 82 } = {}) {
  if (!src) return null;
  if (isDataOrBlob(src) || !isHttpLike(src)) return src;
  try {
    if (typeof buildThumbFromApi === "function") {
      return buildThumbFromApi(src, { w, h, fit, fmt, q }) || src;
    }
  } catch {}
  const params = new URLSearchParams({ src: String(src), w: String(w), h: String(h), fit, fmt, q: String(q) });
  return `${API_BASE}/media/thumbnail/?${params.toString()}`;
}
function normalizeRelated(items) {
  if (!Array.isArray(items)) return [];
  return items.map((it) => {
    const imageAbs = it?.image ? absoluteMedia(it.image) : (it?.imageAbs || null);
    const thumb = imageAbs ? buildThumb(imageAbs, { w: 640, h: 360, fit: "cover", fmt: "webp", q: 82 }) : null;
    return { ...it, imageAbs, thumb };
  });
}

// ================= Быстрые похожие/категория =================
async function fetchCategoryLatest(catSlug, limit = 8) {
  try {
    const res = await fetchCategoryNews(catSlug, 1, limit);
    const arr = Array.isArray(res?.results) ? res.results : Array.isArray(res) ? res : [];
    return normalizeRelated(arr).slice(0, limit);
  } catch {
    return [];
  }
}

async function fetchArticleUniversal(slug) {
  if (!slug) return null;
  try {
    return await getJson(`${API_BASE}/news/${encodeURIComponent(slug)}/`);
  } catch {
    return null;
  }
}

// ================= Быстрый сбор похожих (несколько вариантов) =================
function withTimeout(promise, ms = 1200) {
  return Promise.race([promise, new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms))]);
}
async function fetchJsonArray(url, timeoutMs = 1200, signal) {
  try {
    const d = await withTimeout(getJson(url, { signal }), timeoutMs);
    const arr = Array.isArray(d?.items) ? d.items : Array.isArray(d?.results) ? d.results : Array.isArray(d) ? d : [];
    return normalizeRelated(arr);
  } catch { return []; }
}
async function fetchRelatedVariantsFast(slug, categorySlug, limit = 8, signal) {
  if (!slug) return [];

  // ✅ Вариант 1 (правильный для твоего backend): /news/related/<slug>/
  const p1 = fetchJsonArray(
    `${API_BASE}/news/related/${encodeURIComponent(slug)}/?limit=${limit}&fields=${encodeURIComponent(RELATED_FIELDS)}`,
    1500,
    signal
  );

  // Вариант 2 (на всякий случай, если есть легаси): /news/<slug>/related/
  const p2 = fetchJsonArray(
    `${API_BASE}/news/${encodeURIComponent(slug)}/related/?limit=${limit}&fields=${encodeURIComponent(RELATED_FIELDS)}`,
    1500,
    signal
  );

  // Вариант 3: использовать fetchRelated из ../Api — он умеет перебирать и path, и query
  const p3 = (async () => {
    try {
      const viaNew = await withTimeout(
        (async () => {
          const res = await fetchRelated({ slug, limit, fields: RELATED_FIELDS });
          if (Array.isArray(res?.results)) return normalizeRelated(res.results);
          if (Array.isArray(res)) return normalizeRelated(res);
          return [];
        })(),
        1500
      );
      if (viaNew?.length) return viaNew;
    } catch {}
    try {
      const legacy = await withTimeout(
        (async () => normalizeRelated((await fetchRelated("article", categorySlug || "news", slug)) || []))(),
        1500
      );
      return legacy;
    } catch { return []; }
  })();

  // Вариант 4: быстрая «подушка» — через fetchCategoryNews()
  const p4 = fetchCategoryLatest(categorySlug || "news", limit);

  if (typeof Promise.any === "function") {
    try {
      const first = await Promise.any([
        p1.then((a) => (a?.length ? a : Promise.reject())),
        p2.then((a) => (a?.length ? a : Promise.reject())),
        p3.then((a) => (a?.length ? a : Promise.reject())),
        p4.then((a) => (a?.length ? a : Promise.reject())),
      ]);
      return first.slice(0, limit);
    } catch {
      const [a1, a2, a3, a4] = await Promise.all([p1, p2, p3, p4]);
      const best = [a1, a2, a3, a4].find((a) => a?.length) || [];
      return best.slice(0, limit);
    }
  } else {
    const [a1, a2, a3, a4] = await Promise.allSettled([p1, p2, p3, p4]);
    const pick = (...r) => r.map((x) => (x.status === "fulfilled" ? x.value : [])).find((a) => a?.length) || [];
    return pick(a1, a2, a3, a4).slice(0, limit);
  }
}

// ================= Кеш похожих (memory + sessionStorage) =================
const RELATED_CACHE_TTL = 5 * 60 * 1000;
const relatedCache = new Map();
function ssGet(slug) {
  try {
    const raw = sessionStorage.getItem(`related:${slug}`);
    if (!raw) return null;
    const obj = JSON.parse(raw);
    if (!obj?.ts || !Array.isArray(obj.items)) return null;
    if (Date.now() - obj.ts > RELATED_CACHE_TTL) return null;
    return obj.items;
  } catch { return null; }
}
function ssSet(slug, items) {
  try { sessionStorage.setItem(`related:${slug}`, JSON.stringify({ ts: Date.now(), items })); } catch {}
}
function getCachedRelated(slug) {
  const mem = relatedCache.get(slug);
  if (mem && Date.now() - mem.ts <= RELATED_CACHE_TTL) return mem.items;
  return ssGet(slug);
}
function setCachedRelated(slug, items) {
  relatedCache.set(slug, { ts: Date.now(), items });
  ssSet(slug, items);
}

// ================= Даты/прочее =================
function formatRuPortalDate(isoString, tz = "Europe/Moscow") {
  if (!isoString) return "";
  try {
    const d = new Date(isoString);
    if (Number.isNaN(d.getTime())) return String(isoString);
    const fmt = new Intl.DateTimeFormat("ru-RU", {
      timeZone: tz, day: "numeric", month: "long", year: "numeric",
      hour: "2-digit", minute: "2-digit", hour12: false,
    });
    const parts = {};
    for (const p of fmt.formatToParts(d)) if (p.type !== "literal") parts[p.type] = p.value;
    return `${parts.day} ${parts.month} ${parts.year}, ${parts.hour}:${parts.minute}`;
  } catch { return String(isoString); }
}
function isLikelyISO(v) {
  if (!v) return false;
  const s = String(v).trim();
  return /^\d{4}-\d{2}-\d{2}T/.test(s) || /^\d{4}-\d{2}-\d{2}\s/.test(s);
}
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
  return slug.split("-").map((w) => (w ? w[0].toUpperCase() + w.slice(1) : "")).join(" ");
}
function extractSlug(maybeUrl) {
  if (!maybeUrl) return "";
  try {
    const u = new URL(maybeUrl, BACKEND_ORIGIN);
    const parts = u.pathname.replace(/\/+$/, "").split("/").filter(Boolean);
    return parts[parts.length - 1] || "";
  } catch {
    const parts = String(maybeUrl).replace(/\/+$/, "").split("/").filter(Boolean);
    return parts[parts.length - 1] || "";
  }
}
function filterOutCurrent(list, curSlug, curId) {
  const curSlugLC = (curSlug || "").toLowerCase();
  const curIdStr = curId != null ? String(curId) : null;
  return (Array.isArray(list) ? list : []).filter((n) => {
    const nid = n?.id ?? n?.pk ?? null;
    if (curIdStr && nid != null && String(nid) === curIdStr) return false;
    const nSlug = (n?.slug || n?.news_slug || extractSlug(n?.seo_url) || "").toLowerCase();
    return !(curSlugLC && nSlug && nSlug === curSlugLC);
  });
}

// ================= Источник (логотип/ссылка) =================
function extractDomainHost(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return ""; }
}
function pickSourceFromItem(item) {
  if (!item || typeof item !== "object") return null;
  const sourceTitle =
    item.source_title || item.source_name ||
    (item.source && (item.source.title || item.source.name)) ||
    item.site_name || item.source_domain || item.domain || item.host || null;

  const sourceUrl =
    item.original_url || item.link || item.url ||
    item.source_url || item.source_link || item.source_href ||
    (item.source && (item.source.url || item.source.homepage || item.source.link || item.source.href)) || null;

  if (!sourceTitle && !sourceUrl) return null;

  const domain = sourceUrl ? extractDomainHost(sourceUrl) : "";
  const title = (sourceTitle || "").toString().trim() || domain;
  if (!title) return null;

  const logoPriority =
    item.source_logo || item.source_logo_url ||
    (item.source_fk && (item.source_fk.logo || item.source_fk.icon)) ||
    (item.source && item.source.logo) || null;

  const favicon = domain ? `https://www.google.com/s2/favicons?sz=64&domain_url=${encodeURIComponent("https://" + domain)}` : null;
  return { title, url: sourceUrl, icon: logoPriority || favicon || null };
}

// ================= MetaInfo: дата/время + источник =================
function MetaInfo({ datePretty, dateIso, item }) {
  const hasDate = !!(datePretty && /\d/.test(String(datePretty)));
  const info = pickSourceFromItem(item);

  return (
    <div className={s.metaRow}>
      {hasDate ? (
        <span className={`${s.metaPill} ${s.metaPillTime}`} title={dateIso || datePretty}>
          <FiClock className={s.metaIcon} aria-hidden="true" />
          <time dateTime={dateIso || undefined}>{datePretty}</time>
        </span>
      ) : null}

      {info ? (
        info.url ? (
          <a
            className={`${s.metaPill} ${s.metaPillSource} ${s.metaSourceLink}`}
            href={info.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {info.icon ? (
              <img className={s.metaFav} src={info.icon} alt="" width={16} height={16} />
            ) : (
              <span className={s.sourceDot} aria-hidden="true" />
            )}
            <span className={s.metaSourceLabel}>Источник:&nbsp;</span>
            <span className={s.metaSourceName}>{info.title}</span>
            <FiExternalLink className={s.metaIcon} aria-hidden="true" />
          </a>
        ) : (
          <span className={`${s.metaPill} ${s.metaPillSource}`} aria-label="Источник">
            {info.icon ? <img className={s.metaFav} src={info.icon} alt="" width={16} height={16} /> : <span className={s.sourceDot} aria-hidden="true" />}
            <span className={s.metaSourceLabel}>Источник:&nbsp;</span>
            <span className={s.metaSourceName}>{info.title}</span>
          </span>
        )
      ) : null}
    </div>
  );
}

// ================= ShareButtons: избранное + соцсети + копировать =================
function ShareButtons({ title, slug }) {
  const [copied, setCopied] = useState(false);
  const href = typeof window !== "undefined" ? window.location.href : "";
  const url = encodeURIComponent(href || "");
  const text = encodeURIComponent(title || (typeof document !== "undefined" ? document.title : "") || "");

  const btnStyle = {
    width: 34,
    height: 34,
    borderRadius: 999,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px solid rgba(0,0,0,0.15)",
    background: "transparent",
    cursor: "pointer",
  };

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(href || "");
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch (e) { console.error(e); }
  }

  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
      {/* ❤️ В избранное */}
      <FavoriteHeart slug={slug} kind="sharebar" style={btnStyle} />

      {/* VK */}
      <a
        href={`https://vk.com/share.php?url=${url}&title=${text}`}
        target="_blank"
        rel="noopener noreferrer"
        title="Поделиться во ВКонтакте"
        style={btnStyle}
      >
        <FaVk />
      </a>

      {/* OK */}
      <a
        href={`https://connect.ok.ru/offer?url=${url}&title=${text}`}
        target="_blank"
        rel="noopener noreferrer"
        title="Поделиться в Одноклассниках"
        style={btnStyle}
      >
        <FaOdnoklassniki />
      </a>

      {/* Telegram */}
      <a
        href={`https://t.me/share/url?url=${url}&text=${text}`}
        target="_blank"
        rel="noopener noreferrer"
        title="Поделиться в Telegram"
        style={btnStyle}
      >
        <FaTelegramPlane />
      </a>

      {/* WhatsApp */}
      <a
        href={`https://api.whatsapp.com/send?text=${text}%20${url}`}
        target="_blank"
        rel="noopener noreferrer"
        title="Поделиться в WhatsApp"
        style={btnStyle}
      >
        <FaWhatsapp />
      </a>

      {/* Скопировать ссылку */}
      <button type="button" onClick={copyLink} title={copied ? "Скопировано!" : "Скопировать ссылку"} style={btnStyle}>
        <FiLink />
      </button>
    </div>
  );
}

// ================= Основной компонент =================
export default function NewsDetailPage() {
  const params = useParams();
  const [item, setItem] = useState(null);
  const [latest, setLatest] = useState([]);
  const [latestLoading, setLatestLoading] = useState(true);
  const [related, setRelated] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(true);
  const [error, setError] = useState(null);
  const [catDict, setCatDict] = useState({});
  const [showCover, setShowCover] = useState(true); // ← показывать ли обложку

  const leftRef = useRef(null);
  const mainRef = useRef(null);
  const rightRef = useRef(null);
  const relSentinelRef = useRef(null);         // ← наблюдаем за видимостью «Похожие»
  const latestSlugRef = useRef(null);

  // 🔧 ВАЖНО: по умолчанию разрешаем загрузку «Похожих», observer — лишь доп. триггер
  const [relCanLoad, setRelCanLoad] = useState(true);

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

  // Справочник категорий для хлебных крошек
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

  // Предзагрузка домена бекенда (мелкая оптимизация)
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

  // Ленивая активация блока «Похожие»: больше не блокирует загрузку
  useEffect(() => {
    if (!relSentinelRef.current) return;
    let obs = null;
    const el = relSentinelRef.current;
    const handler = (entries) => {
      const e = entries[0];
      if (e && e.isIntersecting) {
        setRelCanLoad(true);
        if (obs) obs.disconnect();
      }
    };
    obs = new IntersectionObserver(handler, { root: null, rootMargin: "160px 0px", threshold: 0.01 });
    obs.observe(el);
    return () => { if (obs) obs.disconnect(); };
  }, [params?.slug]);

  // Похожие (кеш/категория → быстрые варианты) + AbortController
  useEffect(() => {
    const slug = params?.slug;
    const categoryParam = params?.category || "news";
    if (!slug || !relCanLoad) return;

    let cancelled = false;
    const ac = new AbortController();

    latestSlugRef.current = slug;
    setRelated([]);
    setRelatedLoading(true);

    // Prefetch корректного варианта related
    try {
      const pre = document.createElement("link");
      pre.rel = "prefetch";
      pre.href = `${API_BASE}/news/related/${encodeURIComponent(slug)}/?limit=8&fields=${encodeURIComponent(RELATED_FIELDS)}`;
      document.head.appendChild(pre);
      setTimeout(() => { try { document.head.removeChild(pre); } catch {} }, 5000);
    } catch {}

    // кеш
    const cachedRaw = getCachedRelated(slug);
    const cached = filterOutCurrent(cachedRaw || [], slug, null);
    if (cached?.length) {
      if (latestSlugRef.current === slug && !cancelled) {
        setRelated(cached);
        setRelatedLoading(false);
      }
    }

    // быстрая «подушка» из категории — БЕЗ 404
    (async () => {
      try {
        if (!cached?.length) {
          const catFastRaw = await fetchCategoryLatest(categoryParam, 8);
          const catFast = filterOutCurrent(catFastRaw, slug, null);
          if (!cancelled && latestSlugRef.current === slug && catFast.length) {
            setRelated(catFast);
            setRelatedLoading(false);
          }
        }
      } catch {}
    })();

    // полноценный сбор вариантов
    (async () => {
      try {
        const listRaw = await fetchRelatedVariantsFast(slug, categoryParam, 8, ac.signal);
        const list = filterOutCurrent(listRaw, slug, null);
        if (cancelled || latestSlugRef.current !== slug) return;
        setCachedRelated(slug, list);
        setRelated(list);
      } finally {
        if (!cancelled && latestSlugRef.current === slug) setRelatedLoading(false);
      }
    })();

    return () => { cancelled = true; ac.abort(); };
  }, [params?.slug, params?.category, relCanLoad]);

  // Загрузка самой статьи + «последних»
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const slug = params?.slug;
        const categoryParam = params?.category || "news";
        if (!slug) throw new Error("slug не найден в параметрах");

        let article = null;
        try { article = await fetchArticle(categoryParam, slug); } catch {}
        if (!article) {
          try { article = await fetchArticleUniversal(slug); } catch {}
        }
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
    })();
    return () => { cancelled = true; };
  }, [params?.slug, params?.category]);

  // При смене новости снова разрешаем показывать обложку (если будет валидное фото)
  useEffect(() => {
    setShowCover(true);
    // перезапуск «ленивой» подсказки — но relCanLoad оставляем true, чтобы не блокировать
  }, [params?.slug]);

  // Доктайтл
  useEffect(() => {
    if (!item?.title) return;
    const prev = document.title;
    document.title = buildPrettyTitle(item.title);
    return () => { document.title = prev; };
  }, [item?.title]);

  // Синхронизация высот колонок (в десктопной вёрстке)
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
    return () => {
      try { ro.disconnect(); } catch {}
      window.removeEventListener("resize", syncHeights);
    };
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

  // --- ДАННЫЕ ДЛЯ РЕНДЕРА ---
  const imageRaw = item.image || item.cover_image || item.cover || item.image_url || null;
  const externalUrl = item.original_url || item.link || item.url || null;

  // Контент рендерим всегда, даже если нет фото/обложки — без плейсхолдеров
  const contentHtml = DOMPurify.sanitize(item.content || item.summary || "", { USE_PROFILES: { html: true } });

  const dateCandidate =
    (isLikelyISO(item.pub_date_fmt) && item.pub_date_fmt) ||
    item.published_at || item.date || item.created_at || item.updated_at || item.pub_date_fmt || "";
  const datePrettyRaw = dateCandidate ? formatRuPortalDate(dateCandidate, "Europe/Moscow") : "";
  const datePretty = /\d/.test(String(datePrettyRaw)) ? datePrettyRaw : "";
  const dateIso = isLikelyISO(dateCandidate) ? new Date(dateCandidate).toISOString() : "";

  const categorySlug = item.category?.slug || params?.category || "news";
  const categoryTitle = item.category?.name || item.category?.title || catDict[categorySlug] || humanizeSlug(categorySlug);

  // Готовим урл обложки без заглушек; если битая — скроем через onError
  const coverAbs = imageRaw ? absoluteMedia(imageRaw) : null;
  const coverUrl = coverAbs ? buildThumb(coverAbs, { w: 980, h: 520, q: 85, fmt: "webp", fit: "cover" }) : null;

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

        <MetaInfo datePretty={datePretty} dateIso={dateIso} item={item} />

        {/* Обложка: показываем ТОЛЬКО если есть валидный URL и пока не упали на onError */}
        {coverUrl && showCover ? (
          <img
            src={coverUrl}
            alt={item.title || ""}
            className={s.cover}
            onError={() => setShowCover(false)}
          />
        ) : null}

        {(item.summary || item.content) && (
          <ArticleBody html={contentHtml} baseUrl={externalUrl || ""} className={s.body} />
        )}

        {/* НИЖНИЙ ACTIONS-БЛОК: Читать в источнике + панель с избранным и шарингом */}
        <div className={s.external}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            {externalUrl ? (
              <a className={s.externalLink} href={externalUrl} target="_blank" rel="noreferrer">
                Читать в источнике →
              </a>
            ) : null}

            <div style={{ display: "inline-flex", alignItems: "center", gap: 10, marginLeft: "auto" }}>
              <ShareButtons title={item?.title || ""} slug={item?.slug || params?.slug} />
            </div>
          </div>
        </div>
      </main>

      <aside className={s.rightAside} ref={rightRef}>
        {/* Сентинел для ленивой загрузки «Похожих» (скрытый) */}
        <div
          ref={relSentinelRef}
          style={{ position: "absolute", top: 0, left: 0, width: 1, height: 1, opacity: 0, pointerEvents: "none" }}
        />

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
