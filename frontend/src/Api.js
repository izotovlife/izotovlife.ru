/* Путь: frontend/src/Api.js
   Назначение: Axios-инстанс и функции API (новости, категории, поиск, SEO-маршруты, аутентификация).
   Что внутри (добавлено, ничего важного не удалено):
   - ✅ Горячий фолбэк TEST_FEED: если /api/news/feed/ упал/пусто — показываем тестовые новости.
   - ✅ Тумблер заглушки: localStorage.useFakeFeed = "1" ИЛИ ?fake=1 в URL.
   - ✅ Пагинация фолбэка (page, page_size), совместима с текущим fetchNews().
   - ✅ buildThumbnailUrl(): НЕ шлём в ресайзер data:/blob:/about: и аудио.
   - ✅ Жёсткая нормализация путей категорий + tryGet(), attachSeoUrl(), resolveNewsApi и пр. сохранены.
   - ✅ ДОПОЛНЕНО: fetchNewsFeedText()/fetchNewsFeedImages() с тем же фолбэком (если где-то используются).
*/

import axios from "axios";

// ---------------- БАЗОВАЯ НАСТРОЙКА ----------------
export const API_BASE = "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
});

// ---------------- ФОЛБЭКИ (ТЕСТОВАЯ ЛЕНТА) ----------------
const TEST_FEED = [
  {
    id: 10001,
    slug: "test-1-vilfand-teplie-vyhodnye",
    title: "Вильфанд: ближайшие выходные в Москве будут тёплыми",
    summary: "Синоптик порадовал хорошими новостями: бабье лето затянулось.",
    source: { name: "tass.ru", slug: "tass" },
    category: { name: "Общество", slug: "society" },
    url: "#",
    image: null,
    published_at: new Date().toISOString(),
  },
  {
    id: 10002,
    slug: "test-2-berzon-black-friday",
    title: "Экономист Берзон: «Не покупайте лишнее в чёрную пятницу»",
    summary: "Скидки манят, но бюджет благодарит дисциплину.",
    source: { name: "rt.com", slug: "rt" },
    category: { name: "Экономика", slug: "economy" },
    url: "#",
    image: null,
    published_at: new Date().toISOString(),
  },
  {
    id: 10003,
    slug: "test-3-astor-mirage-ukraine",
    title: "Макрон: Франция поставит Украине ракеты Aster и истребители Mirage",
    summary: "Политические заявления недели — в одной новости.",
    source: { name: "rt.com", slug: "rt" },
    category: { name: "Политика", slug: "politics" },
    url: "#",
    image: null,
    published_at: new Date().toISOString(),
  },
  {
    id: 10004,
    slug: "test-4-parkovka-krysha",
    title: "На вокзале Петербурга крыша парковки рухнула на платформу",
    summary: "Инцидент без пострадавших, ведётся проверка.",
    source: { name: "rg.ru", slug: "rg" },
    category: { name: "Происшествия", slug: "incidents" },
    url: "#",
    image: null,
    published_at: new Date().toISOString(),
  },
  {
    id: 10005,
    slug: "test-5-kpr-modernizacia-teploseti",
    title: "КНР получит 1 млрд ₽ на модернизацию теплосетей",
    summary: "Финансирование направят в 2025–2026 годах.",
    source: { name: "tass.ru", slug: "tass" },
    category: { name: "Экономика", slug: "economy" },
    url: "#",
    image: null,
    published_at: new Date().toISOString(),
  },
  {
    id: 10006,
    slug: "test-6-gorky-park",
    title: "Золотая осень в Москве: кадры из Парка Горького",
    summary: "Фотопрогулка по городу: пока листья не улетели.",
    source: { name: "izotovlife", slug: "izotovlife" },
    category: { name: "Без категории", slug: "uncategorized" },
    url: "#",
    image: null,
    published_at: new Date().toISOString(),
  },
];

function shouldUseFakeFeed() {
  try {
    const ls = localStorage.getItem("useFakeFeed") === "1";
    const url = new URL(window.location.href);
    const qp = url.searchParams.get("fake") === "1";
    return ls || qp;
  } catch {
    return false;
  }
}

function paginate(arr, page = 1, pageSize = 20) {
  const p = Math.max(1, Number(page) || 1);
  const s = Math.max(1, Number(pageSize) || 20);
  const from = (p - 1) * s;
  return arr.slice(from, from + s);
}

// ---------------- JWT УТИЛИТЫ ----------------
function parseJwt(token) {
  try {
    const [, payload] = token.split(".");
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decodeURIComponent(escape(json)));
  } catch {
    return null;
  }
}

function isJwtValid(token) {
  const p = parseJwt(token);
  if (!p || !p.exp) return false;
  return p.exp > Date.now() / 1000 + 5;
}

function applyAuthHeader(token) {
  api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

function dropToken() {
  try {
    localStorage.removeItem("access");
  } catch {}
  delete api.defaults.headers.common["Authorization"];
}

export function setToken(token) {
  if (token && isJwtValid(token)) {
    try {
      localStorage.setItem("access", token);
    } catch {}
    applyAuthHeader(token);
  } else {
    dropToken();
  }
}

// bootstrap из localStorage
try {
  const saved = localStorage.getItem("access");
  if (saved && isJwtValid(saved)) applyAuthHeader(saved);
  else dropToken();
} catch {}

// Перелогин при 401 (без бесконечных циклов)
api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const status = err?.response?.status;
    const config = err?.config || {};
    if (status === 401 && !config._retry) {
      dropToken();
      config._retry = true;
      if (config.headers) {
        delete config.headers["Authorization"];
        delete config.headers.authorization;
      }
      try {
        return await api.request(config);
      } catch (e) {
        return Promise.reject(e);
      }
    }
    return Promise.reject(err);
  }
);

// ---------------- ОБЩИЕ УТИЛИТЫ ----------------
export function normalizeSlug(raw) {
  if (!raw) return raw;
  let v = String(raw).trim();
  try {
    v = decodeURIComponent(v);
  } catch {}
  v = v.replace(/[?#].*$/g, "").replace(/-{2,}/g, "-").replace(/[-/]+$/g, "");
  return v.trim();
}

export function slugCandidates(raw) {
  if (!raw) return [];
  const t = String(raw).trim().replace(/[-/]+$/g, "");
  const norm = normalizeSlug(t);
  return Array.from(new Set([norm, t])).filter(Boolean);
}

/**
 * tryGet(paths, config?)
 * Перебирает массив путей (или одну строку), делает GET, возвращает первый успешный response.
 * Для дебага шлёт warn со статусами — помогает отловить неправильный маршрут.
 */
export async function tryGet(paths, config = {}) {
  const list = typeof paths === "string" ? [paths] : Array.isArray(paths) ? paths : [];
  let lastErr = null;
  for (const p of list) {
    try {
      const r = await api.get(p, config);
      return r;
    } catch (e) {
      console.warn("tryGet fail:", p, e?.response?.status || e?.message);
      lastErr = e;
    }
  }
  if (lastErr) throw lastErr;
  throw new Error("Все варианты путей вернули ошибку");
}

/** attachSeoUrl(obj)
 * Добавляет seo_url вида "/<category>/<slug>" если отсутствует.
 */
export function attachSeoUrl(obj = {}, type = "") {
  try {
    if (!obj || obj.seo_url) return obj;
    const cat =
      (obj.category && obj.category.slug) ||
      (Array.isArray(obj.categories) && obj.categories[0] && obj.categories[0].slug) ||
      obj.category_slug ||
      null;

    const base = cat ? `/${cat}` : "/news";
    if (obj.slug) obj.seo_url = `${base}/${obj.slug}`;
    else if (obj.title)
      obj.seo_url = `${base}/${encodeURIComponent(
        String(obj.title).toLowerCase().replace(/\s+/g, "-")
      )}`;
  } catch {}
  return obj;
}

// ---------------- МЕДИА-УТИЛИТЫ ----------------
const AUDIO_EXT = [".mp3", ".ogg", ".wav", ".m4a", ".aac", ".flac"];

export function isAudioUrl(url) {
  if (!url) return false;
  const u = String(url).toLowerCase().split("?")[0];
  return AUDIO_EXT.some((ext) => u.endsWith(ext));
}

function isHttpLike(url) {
  return /^https?:\/\//i.test(String(url));
}
function isDataOrBlob(url) {
  return /^(data:|blob:|about:)/i.test(String(url || ""));
}

/**
 * buildThumbnailUrl(src, opts?)
 * Возвращает URL ресайзера /api/news/media/thumbnail/ для http(s)-изображений.
 * - НЕ трогаем аудио (вернём null)
 * - НЕ трогаем data:/blob:/about: (вернём исходник как есть)
 * - Корректно кодируем src.
 */
export function buildThumbnailUrl(
  src,
  { w = 640, h = 360, q = 82, fmt = "webp", fit = "cover" } = {}
) {
  if (!src) return null;
  if (isAudioUrl(src)) return null;
  if (isDataOrBlob(src)) return src; // ← главное лекарство от 400
  if (!isHttpLike(src)) return src;

  const base = `${API_BASE}/news/media/thumbnail/`;
  const params = new URLSearchParams({
    src: String(src),
    w: String(w),
    h: String(h),
    q: String(q),
    fmt,
    fit,
  });
  return `${base}?${params.toString()}`;
}

// алиас для старого кода (если где-то импортировали buildThumb)
export const buildThumb = buildThumbnailUrl;

// ---------------- ЛЕНТА ----------------
export async function fetchNews(page = 1, page_size = 20) {
  // Принудительный тестовый режим
  if (shouldUseFakeFeed()) {
    return paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
  }

  try {
    const r = await api.get("/news/feed/", { params: { page, page_size } });
    let data = [];

    if (Array.isArray(r.data)) data = r.data;
    else if (Array.isArray(r.data.results)) data = r.data.results;
    else if (r.data.results && typeof r.data.results === "object")
      data = Object.values(r.data.results);
    else if (Array.isArray(r.data.items)) data = r.data.items;
    else if (r.data?.results?.results) data = r.data.results.results;

    if (!Array.isArray(data) || data.length === 0) {
      console.warn("⚠️ fetchNews: API пусто/неожиданный формат — включаю TEST_FEED");
      return paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
    }
    return data.map((n) => attachSeoUrl(n));
  } catch (err) {
    console.warn("Ошибка загрузки новостей, использую TEST_FEED:", err?.message || err);
    return paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
  }
}

// Дополнительно: правый столбец (если используется отдельно где-то в коде)
export async function fetchNewsFeedText({ page = 1, page_size = 30 } = {}) {
  if (shouldUseFakeFeed()) {
    const results = paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
    return { count: TEST_FEED.length, next: null, previous: null, results };
  }
  try {
    const r = await api.get("/news/feed/text/", { params: { page, page_size } });
    const data =
      (Array.isArray(r.data?.results) && r.data.results) ||
      (Array.isArray(r.data) && r.data) ||
      (Array.isArray(r.data?.items) && r.data.items) ||
      [];
    if (!data.length) {
      const results = paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
      return { count: TEST_FEED.length, next: null, previous: null, results };
    }
    return { count: data.length, next: null, previous: null, results: data.map(attachSeoUrl) };
  } catch {
    const results = paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
    return { count: TEST_FEED.length, next: null, previous: null, results };
  }
}

export async function fetchNewsFeedImages({ page = 1, page_size = 20 } = {}) {
  if (shouldUseFakeFeed()) {
    const results = paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
    return { count: TEST_FEED.length, next: null, previous: null, results };
  }
  try {
    const r = await api.get("/news/feed/images/", { params: { page, page_size } });
    const data =
      (Array.isArray(r.data?.results) && r.data.results) ||
      (Array.isArray(r.data) && r.data) ||
      (Array.isArray(r.data?.items) && r.data.items) ||
      [];
    if (!data.length) {
      const results = paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
      return { count: TEST_FEED.length, next: null, previous: null, results };
    }
    return { count: data.length, next: null, previous: null, results: data.map(attachSeoUrl) };
  } catch {
    const results = paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
    return { count: TEST_FEED.length, next: null, previous: null, results };
  }
}

// ---------------- КАТЕГОРИИ ----------------
export async function fetchCategories() {
  try {
    const r = await tryGet(["/categories/", "/news/categories/", "/news/category-list/"]);
    const data = r.data;
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.results)) return data.results;
    if (data && typeof data === "object" && data.results) {
      return Array.isArray(data.results) ? data.results : Object.values(data.results);
    }
    console.warn("⚠️ fetchCategories: неожиданный формат ответа", data);
    return [];
  } catch (err) {
    console.error("Ошибка загрузки категорий:", err);
    return [];
  }
}

/** Быстрый батч-эндпоинт обложек категорий.
 * Если нет — вернём {} (фронт сам сделает fallback).
 */
export async function fetchCategoryCovers() {
  try {
    const r = await api.get("/categories/covers/");
    const data = r.data;
    if (Array.isArray(data)) {
      const m = {};
      for (const x of data) if (x && x.slug) m[x.slug] = x.image || "";
      return m;
    }
    if (data && typeof data === "object") return data;
    return {};
  } catch {
    return {};
  }
}

/** Фолбэк-обложка категории из /news/feed/images/?category=<slug>&limit=1 */
export async function fetchFirstImageForCategory(slug) {
  if (!slug) return null;
  try {
    const r = await api.get("/news/feed/images/", { params: { category: slug, limit: 1 } });
    const raw =
      r.data?.items || r.data?.results || (Array.isArray(r.data) ? r.data : []);
    const first = Array.isArray(raw) ? raw[0] : null;
    if (!first) return null;

    const src =
      first.image ||
      first.cover_image ||
      first.cover ||
      first.image_url ||
      first.thumbnail ||
      null;

    return src || null;
  } catch (e) {
    console.warn("fetchFirstImageForCategory: нет фолбэка для", slug, e?.message || e);
    return null;
  }
}

/**
 * fetchCategoryNews(slug, opts)
 * opts может быть:
 *   - числом (page)
 *   - объектом { page=1, limit, allowLegacySlugRoute=false }
 */
export async function fetchCategoryNews(slug, opts = 1) {
  if (!slug) return [];
  const page = typeof opts === "number" ? opts : Number(opts?.page || 1);
  const limit = typeof opts === "object" && opts?.limit ? Number(opts.limit) : undefined;
  const allowLegacy = Boolean(typeof opts === "object" && opts?.allowLegacySlugRoute);

  const encoded = encodeURIComponent(slug);

  const paths = [
    `/news/category/${encoded}/`, // ← правильный маршрут
    `/category/${encoded}/`,
    ...(allowLegacy ? [`/news/${encoded}/`] : []), // ← устаревший
  ];

  const params = limit ? { page, limit } : { page };

  // Если включён общий фейк — фильтруем TEST_FEED по категории
  if (shouldUseFakeFeed()) {
    const filtered = TEST_FEED.filter(
      (i) => (i.category?.slug || "").toLowerCase() === String(slug).toLowerCase()
    );
    const arr = filtered.length ? filtered : TEST_FEED;
    return paginate(arr, page, limit || 20).map((n) => attachSeoUrl(n));
  }

  try {
    const r = await tryGet(paths, { params });
    let data = [];

    if (Array.isArray(r.data)) data = r.data;
    else if (Array.isArray(r.data.results)) data = r.data.results;
    else if (r.data?.results?.results) data = r.data.results.results;
    else if (Array.isArray(r.data.items)) data = r.data.items;
    else if (r.data && typeof r.data === "object" && Array.isArray(r.data.results?.items))
      data = r.data.results.items;

    if (!Array.isArray(data) || data.length === 0) {
      console.warn("⚠️ fetchCategoryNews: API пусто — включаю TEST_FEED (фильтр по категории).");
      const filtered = TEST_FEED.filter(
        (i) => (i.category?.slug || "").toLowerCase() === String(slug).toLowerCase()
      );
      const arr = filtered.length ? filtered : TEST_FEED;
      return paginate(arr, page, limit || 20).map((n) => attachSeoUrl(n));
    }
    return data.map((n) => attachSeoUrl(n));
  } catch (err) {
    console.error("Ошибка загрузки новостей категории, TEST_FEED:", err?.message || err);
    const filtered = TEST_FEED.filter(
      (i) => (i.category?.slug || "").toLowerCase() === String(slug).toLowerCase()
    );
    const arr = filtered.length ? filtered : TEST_FEED;
    return paginate(arr, page, limit || 20).map((n) => attachSeoUrl(n));
  }
}

// ---------------- ПОИСК ----------------
export async function searchAll(query, { limit = 30, offset = 0 } = {}) {
  if (!query) return { items: [], total: 0 };
  try {
    const r = await api.get("/news/search/", { params: { q: query, limit, offset } });
    const items = r.data.results || r.data.items || [];
    return { items: items.map((n) => attachSeoUrl(n)), total: r.data.count ?? items.length };
  } catch (e) {
    console.error("Ошибка поиска:", e);
    return { items: [], total: 0 };
  }
}

export async function fetchSmartSearch(query) {
  if (!query || query.length < 2) return [];
  try {
    const r = await api.get("/news/search/smart/", {
      params: { q: query },
      timeout: 5000,
    });
    const results = Array.isArray(r.data?.results)
      ? r.data.results
      : Array.isArray(r.data)
      ? r.data
      : [];
    return results.map((n) => attachSeoUrl(n));
  } catch {
    return [];
  }
}

// ---------------- СТАТЬИ И РЕЗОЛВЕР ----------------
export async function resolveNews(slug) {
  if (!slug) throw new Error("resolveNews: пустой slug");
  const norm = normalizeSlug(slug);
  const paths = [
    `/news/resolve/${encodeURIComponent(norm)}/`,
    `/news/by-slug/${encodeURIComponent(norm)}/`,
  ];
  const r = await tryGet(paths);
  return r.data;
}
export { resolveNews as resolveNewsApi };

export async function fetchArticle(arg1, arg2) {
  let category, slug;
  if (typeof arg1 === "object" && arg1 !== null) {
    category = arg1.category;
    slug = arg1.slug;
  } else {
    category = arg1;
    slug = arg2;
  }

  if (!slug) throw new Error("fetchArticle: нужен slug");
  const cat = category || "news";
  const cands = slugCandidates(slug);

  // 1) через резолвер
  try {
    const resolved = await resolveNews(cands[0] || slug);
    const detail = resolved?.detail_url;
    if (detail) {
      const r = await api.get(detail);
      return attachSeoUrl(r.data, "article");
    }
  } catch {}

  // 2) фолбэки
  const paths = [
    ...cands.flatMap((s) => [
      `/news/article/${encodeURIComponent(cat)}/${encodeURIComponent(s)}/`,
      `/news/${encodeURIComponent(cat)}/${encodeURIComponent(s)}/`,
      `/news/${encodeURIComponent(s)}/`,
      `/article/${encodeURIComponent(s)}/`,
    ]),
  ];

  const r = await tryGet(paths);
  return attachSeoUrl(r.data, "article");
}

export async function fetchImportedNews(source, slug) {
  if (!source || !slug) throw new Error("fetchImportedNews: нужен source и slug");
  const cands = slugCandidates(slug);
  const paths = cands.map(
    (s) => `/news/rss/${encodeURIComponent(source)}/${encodeURIComponent(s)}/`
  );
  const r = await tryGet(paths);
  return attachSeoUrl(r.data, "rss");
}

// ---------------- ПОХОЖИЕ НОВОСТИ ----------------
export async function fetchRelated(...args) {
  let slug = null;
  let limit = 6;

  if (args.length === 1 && typeof args[0] === "object" && args[0] !== null) {
    slug = args[0].slug;
    if (args[0].limit != null) limit = args[0].limit;
  } else if (args.length >= 1 && typeof args[0] === "string") {
    slug = args[0];
    if (typeof args[1] === "number") limit = args[1];
  }

  let legacy = null;
  if (!slug && args.length >= 3) {
    const [, param, legacySlug] = args;
    legacy = { param, slug: legacySlug };
    slug = legacySlug;
  }

  if (!slug) throw new Error("fetchRelated: нужен slug");

  const cands = slugCandidates(slug);

  const universalFirst = [
    ...cands.map((s) => `/news/related/${encodeURIComponent(s)}/`),
    ...cands.map((s) => `/news/${encodeURIComponent(s)}/related/`),
  ];

  try {
    const r = await tryGet(universalFirst, { params: { limit } });
    const data = r.data?.results || r.data || [];
    return Array.isArray(data) ? data.map((n) => attachSeoUrl(n)) : data;
  } catch {}

  if (legacy && legacy.param) {
    const rssPaths = cands.map(
      (s) =>
        `/news/rss/${encodeURIComponent(legacy.param)}/${encodeURIComponent(s)}/related/`
    );
    const articlePaths = cands.map(
      (s) =>
        `/news/article/${encodeURIComponent(legacy.param)}/${encodeURIComponent(
          s
        )}/related/`
    );
    const universalPaths = cands.map(
      (s) =>
        `/news/${encodeURIComponent(legacy.param)}/${encodeURIComponent(s)}/related/`
    );
    const paths = [...articlePaths, ...rssPaths, ...universalPaths];
    const r2 = await tryGet(paths, { params: { limit } });
    const data2 = r2.data?.results || r2.data || [];
    return Array.isArray(data2) ? data2.map((n) => attachSeoUrl(n)) : data2;
  }

  return [];
}

// ---------------- МЕТРИКИ ----------------
export async function hitMetrics(type, slug) {
  try {
    const normType = type === "a" ? "article" : type === "i" ? "rss" : type;
    const cands = slugCandidates(slug);
    const s = cands[0] || normalizeSlug(slug);
    const r = await api.post("/news/metrics/hit/", { type: normType, slug: s });
    return r.data;
  } catch (e) {
    console.error("metrics/hit error", e);
    return null;
  }
}

// ---------------- СТРАНИЦЫ ----------------
export async function fetchPages() {
  try {
    const r = await api.get("/pages/");
    return r.data;
  } catch (err) {
    console.error("fetchPages error", err);
    return [];
  }
}
export async function fetchPage(slug) {
  try {
    const r = await api.get(`/pages/${slug}/`);
    return r.data;
  } catch (err) {
    console.error("fetchPage error", err);
    return null;
  }
}

// ---------------- ПРЕДЛОЖИТЬ НОВОСТЬ ----------------
export async function suggestNews(payload) {
  try {
    const r = await api.post("/news/suggest/", payload, {
      headers: { "Content-Type": "application/json" },
      timeout: 15000,
    });
    return r.data;
  } catch (e) {
    if (e.response?.data) throw e.response.data;
    throw new Error(e.message || "Network error");
  }
}

// ---------------- АУТЕНТИФИКАЦИЯ ----------------
export async function login(username, password) {
  const r = await api.post("/auth/login/", { username, password });
  const token = r.data?.access;
  if (token) setToken(token);
  return r.data;
}
export async function register(data) {
  const r = await api.post("/auth/register/", data);
  return r.data;
}
export async function whoami() {
  try {
    const token = localStorage.getItem("access");
    if (!token || !isJwtValid(token)) return null;
    const r = await api.get("/auth/me/");
    return r.data;
  } catch {
    return null;
  }
}

// ---------------- АДМИН-СЕССИЯ ----------------
export async function adminSessionLogin() {
  const r = await api.post("/security/admin-session-login/");
  return r.data;
}
export async function goToAdmin() {
  try {
    const r = await adminSessionLogin();
    let url = r.admin_url;
    if (url.startsWith("/")) {
      const base = api.defaults.baseURL.replace(/\/api$/, "");
      url = base + url;
    }
    window.location.href = url;
  } catch (err) {
    console.error("Не удалось открыть админку:", err);
  }
}

export default api;
