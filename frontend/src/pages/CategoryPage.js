// Путь: frontend/src/pages/CategoryPage.js
// Назначение: Страница категорий (/categories) и одной категории (/:slug).
// Исправления/добавления:
//   ✅ Починен warning ESLint (react-hooks/exhaustive-deps): вместо прямого чтения covers в эффекте — снимок через coversRef
//   ✅ Убрана ошибочная строка-метка `theCovers:` (ранее чинили SyntaxError)
//   ✅ Хелпер withTitleParts вынесен за пределы хуков (ESLint)
//   ✅ Фолбэк-обложка: fetchFirstImageForCategory() из /news/feed/images/?category=<slug>&limit=1
//   ✅ Фильтрация аудио: isAudioUrl() — аудио-URL не считаем обложкой
//   ✅ Обложки через SmartMedia: изображения идут через ресайзер, аудио — нет
//   ⚠️ Остальная логика (батч-обложки, кэш, скелетоны, ленивая лента и «входящие») сохранена

import React, { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useLocation, Link } from "react-router-dom";
import InfiniteScroll from "react-infinite-scroll-component";
import s from "./CategoryPage.module.css";

import {
  fetchCategoryNews,
  fetchCategories,
  fetchCategoryCovers,
  fetchFirstImageForCategory,
  isAudioUrl,
} from "../Api";
import NewsCard from "../components/NewsCard";
import SourceLabel from "../components/SourceLabel";
import IncomingNewsTray from "../components/IncomingNewsTray";
import SmartMedia from "../components/SmartMedia";

const COVERS_CACHE_KEY = "cat_covers_v1";
const COVERS_TTL_MS = 10 * 60 * 1000;

/* =========================
   ВНЕКОМПОНЕНТНЫЕ ХЕЛПЕРЫ
   ========================= */
const imageFromItem = (n) =>
  n?.image || n?.cover_image || n?.preview_image || n?.thumbnail || n?.photo || "";

// Аудио не подходит как «обложка» категории
const isImageOk = (url) => {
  if (!url) return false;
  const u = String(url);
  if (u.includes("default_news.svg")) return false;
  if (isAudioUrl(u)) return false;
  return true;
};

/** Эвристика «популярности» — выбираем лучшую обложку */
const chooseBestCover = (items) => {
  let bestUrl = "";
  let bestScore = -1;
  for (const it of items || []) {
    const url = imageFromItem(it);
    if (!isImageOk(url)) continue;
    const score =
      (Number(it.views) || Number(it.hits) || 0) * 1 +
      (Number(it.rank) || 0) * 100 +
      (Number(it.comments_count) || Number(it.comments) || 0) * 10 +
      (Number(it.likes) || 0) * 5 +
      (Number(it.shares) || 0) * 5;
    if (score > bestScore) {
      bestScore = score;
      bestUrl = url;
    }
  }
  if (!bestUrl) {
    const first = (items || []).find((x) => isImageOk(imageFromItem(x)));
    if (first) bestUrl = imageFromItem(first);
  }
  return bestUrl;
};

/** Разбиваем заголовок на части по «//», чтобы красиво резать длинные */
function withTitleParts(items) {
  return (items || []).map((item) => ({
    ...item,
    titleParts: (item.title || "").split("//").map((t) => t.trim()),
  }));
}

export default function CategoryPage() {
  const { slug } = useParams();
  const location = useLocation();

  const isListMode =
    !slug || location.pathname === "/categories" || location.pathname.startsWith("/categories/");

  // --- индекс категорий
  const [allCategories, setAllCategories] = useState([]);
  const [covers, setCovers] = useState({});
  const coversRef = useRef(covers);            // ⚠️ снимок covers для эффектов
  useEffect(() => { coversRef.current = covers; }, [covers]); // синхронизация снимка
  const [catsLoading, setCatsLoading] = useState(true);

  // --- страница одной категории
  const [photoNews, setPhotoNews] = useState([]);
  const [textNews, setTextNews] = useState([]);
  const [categoryName, setCategoryName] = useState(slug || "Категории");
  const [loading, setLoading] = useState(true);

  const pageRef = useRef(1);
  const loadingRef = useRef(false);
  const [hasMore, setHasMore] = useState(true);
  const hasMoreRef = useRef(true);
  useEffect(() => {
    hasMoreRef.current = hasMore;
  }, [hasMore]);

  const gridRef = useRef(null);
  const [prefilled, setPrefilled] = useState(false);

  const [incoming, setIncoming] = useState([]);
  const lastTopKeyRef = useRef(null);

  // ---------- утилиты ----------
  const hasSomeText = useCallback((n) => {
    if (!n) return false;
    const clean = (htmlOrText) => {
      const tmp = document.createElement("div");
      tmp.innerHTML = htmlOrText || "";
      let plain = (tmp.textContent || tmp.innerText || "").toLowerCase();
      plain = plain
        .replace(/\u00a0|\u202f/g, " ")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/^[.,!?:;\-—–\s]+|[.,!?:;\-—–\s]+$/g, "");
      return plain;
    };
    const title = clean(n.title || "");
    const body = clean(
      n.summary ||
        n.description ||
        n.text ||
        n.body ||
        n.content ||
        n.content_html ||
        n.lead ||
        n.short_text ||
        ""
    );
    const isStop = (s) =>
      !s ||
      s === "без текста" ||
      s === "нет текста" ||
      s === "no text" ||
      s === "notext" ||
      s === "n/a" ||
      s === "-" ||
      s === "—" ||
      s === "–";
    const MIN_LEN = 8;
    const okTitle = !!title && !isStop(title);
    const okBody = !!body && !isStop(body) && body.length >= MIN_LEN;
    return okTitle || okBody;
  }, []);

  // Имя категории
  useEffect(() => {
    let mounted = true;
    async function loadCategoryName() {
      try {
        const cats = await fetchCategories();
        const found = Array.isArray(cats) ? cats.find((c) => c.slug === slug) : null;
        if (mounted) setCategoryName(found?.name || found?.title || slug);
      } catch {
        if (mounted) setCategoryName(slug);
      }
    }
    if (isListMode) {
      setCategoryName("Категории");
    } else if (slug) {
      loadCategoryName();
    }
    return () => {
      mounted = false;
    };
  }, [slug, isListMode]);

  // Сброс при смене категории
  useEffect(() => {
    if (isListMode) return;
    setPhotoNews([]);
    setTextNews([]);
    setHasMore(true);
    setLoading(true);
    setPrefilled(false);
    setIncoming([]);
    lastTopKeyRef.current = null;
    pageRef.current = 1;
  }, [slug, isListMode]);

  // Ленивая подгрузка ленты категории
  const loadMore = useCallback(async () => {
    if (isListMode) return;
    if (!slug) return;
    if (loadingRef.current || !hasMoreRef.current) return;

    try {
      loadingRef.current = true;
      const page = pageRef.current;

      const data = await fetchCategoryNews(slug, page);
      const results = Array.isArray(data)
        ? data
        : Array.isArray(data?.results)
        ? data.results
        : [];

      const valid = results.filter(hasSomeText);
      const withPhoto = valid.filter((n) => isImageOk(imageFromItem(n)));
      const withoutPhoto = valid.filter((n) => !isImageOk(imageFromItem(n)));

      const withPhotoProcessed = withTitleParts(withPhoto);
      const withoutPhotoProcessed = withTitleParts(withoutPhoto);

      const seen = new Set(
        photoNews.map((n) => n?.id ?? n?.slug ?? null).concat(textNews.map((n) => n?.id ?? n?.slug ?? null)).filter(Boolean)
      );
      const uniquePhoto = withPhotoProcessed.filter((n) => !seen.has(n?.id ?? n?.slug ?? null));
      const uniqueText = withoutPhotoProcessed.filter((n) => !seen.has(n?.id ?? n?.slug ?? null));

      setPhotoNews((prev) => [...prev, ...uniquePhoto]);
      setTextNews((prev) => [...prev, ...uniqueText]);

      if (page === 1) {
        const top = valid[0];
        if (top) lastTopKeyRef.current = top?.id ?? top?.slug ?? null;
      }

      const more = results.length > 0;
      setHasMore(more);
      hasMoreRef.current = more;
      pageRef.current = page + 1;
    } catch {
      setHasMore(false);
      hasMoreRef.current = false;
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, [slug, isListMode, hasSomeText, photoNews, textNews]);

  // Первичная загрузка ленты
  useEffect(() => {
    if (isListMode) return;
    if (!slug) return;
    loadMore();
  }, [slug, isListMode, loadMore]);

  // Предзаполнение
  useEffect(() => {
    if (isListMode) return;
    if (prefilled) return;
    if (photoNews.length === 0 && textNews.length === 0) return;

    let cancelled = false;
    const fill = async () => {
      await new Promise((r) => requestAnimationFrame(r));
      for (let i = 0; i < 2; i++) {
        if (cancelled || !hasMoreRef.current) break;

        const grid = gridRef.current;
        const height = grid?.getBoundingClientRect().height || 0;

        const needMore = photoNews.length < 6 || height < window.innerHeight * 1.1;

        if (!needMore) {
          setPrefilled(true);
          break;
        }
        await loadMore();
      }
    };

    fill();
    return () => {
      cancelled = true;
    };
  }, [isListMode, photoNews.length, textNews.length, prefilled, loadMore]);

  // Входящие
  const pollIncoming = useCallback(async () => {
    if (isListMode) return;
    try {
      const data = await fetchCategoryNews(slug, 1);
      const results = Array.isArray(data)
        ? data
        : Array.isArray(data?.results)
        ? data.results
        : [];
      const valid = results.filter(hasSomeText);
      if (!valid.length) return;

      if (!lastTopKeyRef.current) {
        lastTopKeyRef.current = valid[0]?.id ?? valid[0]?.slug ?? null;
        return;
      }

      const collected = [];
      for (const n of valid) {
        const key = n?.id ?? n?.slug ?? null;
        if (!key) continue;
        if (key === lastTopKeyRef.current) break;
        collected.push(n);
      }

      if (collected.length) {
        const collectedProcessed = withTitleParts(collected);
        setIncoming((prev) => [...collectedProcessed, ...prev]);
        lastTopKeyRef.current = valid[0]?.id ?? valid[0]?.slug ?? lastTopKeyRef.current;
      }
    } catch {}
  }, [slug, isListMode, hasSomeText]);

  useEffect(() => {
    if (isListMode) return;
    const t = setInterval(pollIncoming, 20000);
    return () => clearInterval(t);
  }, [isListMode, pollIncoming]);

  // ===== ИНДЕКС КАТЕГОРИЙ =====

  // 1) Загрузка списка категорий + кэш обложек + быстрый фолбэк из feed/images
  useEffect(() => {
    if (!isListMode) return;
    let mounted = true;

    (async () => {
      try {
        setCatsLoading(true);

        const cats = await fetchCategories();
        if (mounted) setAllCategories(Array.isArray(cats) ? cats : []);

        // 1) Кэш
        try {
          const raw = sessionStorage.getItem(COVERS_CACHE_KEY);
          if (raw) {
            const parsed = JSON.parse(raw);
            if (parsed && parsed.ts && Date.now() - parsed.ts < COVERS_TTL_MS && parsed.map) {
              if (mounted) setCovers(parsed.map);
            }
          }
        } catch {}

        // 2) Быстрый батч с бэка
        const serverMap = await fetchCategoryCovers();
        if (mounted && serverMap && Object.keys(serverMap).length) {
          setCovers((prev) => {
            const next = { ...serverMap, ...prev };
            try {
              sessionStorage.setItem(COVERS_CACHE_KEY, JSON.stringify({ ts: Date.now(), map: next }));
            } catch {}
            return next;
          });
        }

        // 3) Быстрый фолбэк: для тех, у кого обложки нет — возьмём первую картинку из feed/images
        const needFallback = (cats || [])
          .map((c) => c.slug)
          .filter(Boolean)
          .filter((sl) => !serverMap?.[sl] && coversRef.current[sl] === undefined); // ← читаем снимок
        for (const sl of needFallback) {
          try {
            const img = await fetchFirstImageForCategory(sl);
            if (mounted && isImageOk(img)) {
              setCovers((prev) => {
                const next = { ...prev, [sl]: img };
                try {
                  sessionStorage.setItem(COVERS_CACHE_KEY, JSON.stringify({ ts: Date.now(), map: next }));
                } catch {}
                return next;
              });
            }
          } catch {}
        }
      } finally {
        if (mounted) setCatsLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [isListMode]); // ✅ нет предупреждений, т.к. covers читаем через ref

  // 2) Доп. Fallback: подгружаем обложки пакетами из содержимого категории (эвристика выбора лучшей)
  useEffect(() => {
    if (!isListMode) return;
    if (!allCategories.length) return;

    let cancelled = false;

    const scheduleIdle = (fn) => {
      if ("requestIdleCallback" in window) {
        // @ts-ignore
        window.requestIdleCallback(() => !cancelled && fn(), { timeout: 1500 });
      } else {
        setTimeout(() => !cancelled && fn(), 250);
      }
    };

    const toLoadAll = allCategories
      .map((c) => c.slug)
      .filter(Boolean)
      .filter((sl) => covers[sl] === undefined); // читаем текущее значение — и этот эффект завязан на covers

    if (!toLoadAll.length) return;

    const worker = async (sl) => {
      try {
        const data = await fetchCategoryNews(sl, 1);
        const items = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
        const best = chooseBestCover(items);
        const img = isImageOk(best) ? best : "";
        if (!cancelled) {
          setCovers((prev) => {
            const next = { ...prev, [sl]: img };
            try {
              sessionStorage.setItem(COVERS_CACHE_KEY, JSON.stringify({ ts: Date.now(), map: next }));
            } catch {}
            return next;
          });
        }
      } catch {
        if (!cancelled) {
          setCovers((prev) => {
            const next = { ...prev, [sl]: "" };
            try {
              sessionStorage.setItem(COVERS_CACHE_KEY, JSON.stringify({ ts: Date.now(), map: next }));
            } catch {}
            return next;
          });
        }
      }
    };

    const runBatches = async (slugs, parallel = 4) => {
      let i = 0;
      const runners = Array.from({ length: Math.min(parallel, slugs.length) }, async () => {
        while (i < slugs.length && !cancelled) {
          const current = slugs[i++];
          // eslint-disable-next-line no-await-in-loop
          await worker(current);
        }
      });
      await Promise.all(runners);
    };

    const first = toLoadAll.slice(0, 8);
    const rest = toLoadAll.slice(8);

    runBatches(first, 4).then(() => {
      if (rest.length) scheduleIdle(() => runBatches(rest, 3));
    });

    return () => {
      cancelled = true;
    };
  }, [isListMode, allCategories, covers]); // chooseBestCover — стабильный вне компонента

  // ===== РЕНДЕР =====
  if (isListMode) {
    return (
      <div className={`${s.page} max-w-7xl mx-auto py-6`}>
        <nav className={s.breadcrumbs}>
          <Link to="/">Главная</Link> <span>›</span> <span>Категории</span>
        </nav>

        <h1 className={s.title}>Категории</h1>

        {catsLoading ? (
          <p className="text-gray-400">Загрузка…</p>
        ) : allCategories.length === 0 ? (
          <p className={s.empty}>Категории не найдены.</p>
        ) : (
          <div className={s.catGrid}>
            {allCategories.map((cat, idx) => {
              const slug = cat.slug;
              const rawCover = covers[slug] || "";
              // Не показываем аудио как обложку
              const cover = isImageOk(rawCover) ? rawCover : "";
              const name = cat.name || cat.title || slug;
              return (
                <Link
                  key={cat.id ?? slug ?? idx}
                  to={`/${slug}/`}
                  className={`${s.catCard} ${cover ? "" : s.skeleton}`}
                >
                  {cover ? (
                    <div className={s.catImageWrap}>
                      {/* SmartMedia сам отправит изображение через ресайзер и НЕ будет трогать аудио */}
                      <SmartMedia
                        src={cover}
                        alt={name}
                        w={800}
                        h={450}
                        className={s.catImage}
                        style={{ display: "block", width: "100%", height: "auto" }}
                      />
                    </div>
                  ) : null}
                  <div className={s.catOverlay} />
                  <div className={s.catLabel}>
                    <div className={s.catName}>{name}</div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  // === РЕЖИМ ОДНОЙ КАТЕГОРИИ ===
  return (
    <div className={`${s.page} max-w-7xl mx-auto py-6`}>
      <nav className={s.breadcrumbs}>
        <Link to="/">Главная</Link> <span>›</span> <span>{categoryName}</span>
      </nav>

      <h1 className={s.title}>{categoryName}</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <InfiniteScroll
            dataLength={photoNews.length}
            next={loadMore}
            hasMore={hasMore}
            loader={<p className="text-gray-400">Загрузка...</p>}
            endMessage={<p className="text-gray-400 mt-4">Больше новостей нет</p>}
            scrollThreshold="1200px"
          >
            <div ref={gridRef} className={s["news-grid"]}>
              {photoNews.map((item, idx) => (
                <NewsCard
                  key={`${item.id ?? item.slug ?? idx}-${idx}`}
                  item={item}
                  eager={idx < 6}
                />
              ))}
            </div>
          </InfiniteScroll>
        </div>

        <div>
          {loading && textNews.length === 0 ? (
            <p className="text-gray-400">Загрузка...</p>
          ) : textNews.length === 0 ? (
            <p className={s.empty}>Новости без иллюстрации не найдены.</p>
          ) : (
            <ul className="space-y-3">
              {textNews.map((n, idx) => (
                <li
                  key={`text-${n.id ?? n.slug ?? idx}-${idx}`}
                  className="border-b border-gray-700 pb-2"
                >
                  <Link
                    to={n.seo_url ?? `/${n.category?.slug ?? slug}/${n.slug}/`}
                    className="block hover:underline text-sm font-medium"
                  >
                    {n.titleParts ? n.titleParts[0] : n.title}
                  </Link>
                  <SourceLabel item={n} className="text-xs text-gray-400" />
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <IncomingNewsTray
        items={incoming}
        maxRows={3}
        gap={8}
        renderItem={(n) => (
          <Link
            to={n.seo_url ?? `/${n.category?.slug ?? slug}/${n.slug}/`}
            className="no-underline"
            style={{ color: "inherit" }}
          >
            <div style={{ fontWeight: 600, marginBottom: 4 }}>
              {n.titleParts ? n.titleParts[0] : n.title}
            </div>
            <div style={{ fontSize: 12, opacity: 0.7 }}>
              {n.source?.name || n.source || "Источник неизвестен"}
            </div>
          </Link>
        )}
      />
    </div>
  );
}
