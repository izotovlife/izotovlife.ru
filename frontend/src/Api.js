// Путь: frontend/src/Api.js
// Назначение: Axios-инстанс и все функции API (новости, категории, поиск, SEO-маршруты, избранное, аутентификация, метрики).
// Что внутри (полный файл):
// - axios-инстанс с базой из REACT_APP_API_BASE или http://127.0.0.1:8000/api
// - Именованный экспорт http (alias api) + default export api — совместимость
// - buildThumbnailUrl() → /api/media/thumbnail/?src=... (НЕ для data:/blob:/about:; аудио не шлём в ресайзер)
//   ⚠️ ДОБАВЛЕНО: относительные пути /media/... теперь превращаются в абсолютные к Django и идут через ресайзер
// - DEFAULT_NEWS_PLACEHOLDER (data:URI SVG) + buildThumbnailOrPlaceholder()
// - TEST_FEED (localStorage.useFakeFeed=1 или ?fake=1) с пагинацией
// - tryGet/tryPost — перебор маршрутов с «тихими» статусами (400/401/404/405)
// - canonSlug() алиасы (obschestvo→obshchestvo, proisshestvija→proisshestviya, lenta-novostej→lenta-novostey)
// - fetchCategoryNews(): сначала path-ручки, затем feed-квери; предохранитель CAT_STOP_AFTER
// - fetchArticle() гибкий; fetchRelated() перебирает маршруты
// - Избранное/аутентификация/метрики/страницы — всё как было
// ДОБАВЛЕНО для тишины/совместимости:
//   ✓ Request-интерсептор axios и патч window.fetch (см. низ файла)
//   ✓ Обратные алиасы для проблемных слагов категорий
//   ✓ ИНТЕРСЕПТОР ДЛЯ FormData: при отправке FormData удаляем жёсткий Content-Type (чтобы axios выставил boundary)
//   ✓ suggestNews(): авто-сборка FormData из объекта, корректная отправка файлов и токена капчи (без принудительного JSON)
//   ✓ ЭКСПОРТЫ FRONTEND_BASE_URL и FRONTEND_LOGIN_URL (совместимость со старыми компонентами)
//   ✓ Переписчик URL учитывает /api/news/check/ и /api/favorites/* → переводит в query-форму (?slug=...), чтобы убрать 404

import axios from "axios";

/* ---------------- БАЗА И ИНСТАНС ---------------- */
export const API_BASE = (
  process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000/api"
).replace(/\/$/, "");

// 🔗 Фронтендные урлы для совместимости со старыми компонентами (например, FavoriteHeart)
export const FRONTEND_BASE_URL =
  (typeof window !== "undefined" && window.location?.origin) ||
  process.env.REACT_APP_FRONTEND_BASE_URL ||
  "http://localhost:3000";
export const FRONTEND_LOGIN_URL =
  process.env.REACT_APP_FRONTEND_LOGIN_URL || "/login";

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
});

// совместимость со старыми импортами
export { api as http };

/* ---------------- ТЕСТОВАЯ ЛЕНТА (ФОЛБЭК) ---------------- */
const TEST_FEED = [
  { id: 10001, slug: "test-1-vilfand-teplie-vyhodnye", title: "Вильфанд: ближайшие выходные в Москве будут тёплыми", summary: "Синоптик порадовал хорошими новостями: бабье лето затянулось.", source: { name: "tass.ru", slug: "tass" }, category: { name: "Общество", slug: "obshchestvo" }, url: "#", image: null, published_at: new Date().toISOString() },
  { id: 10002, slug: "test-2-berzon-black-friday", title: "Экономист Берзон: «Не покупайте лишнее в чёрную пятницу»", summary: "Скидки манят, но бюджет благодарит дисциплину.", source: { name: "rt.com", slug: "rt" }, category: { name: "Экономика", slug: "ekonomika" }, url: "#", image: null, published_at: new Date().toISOString() },
  { id: 10003, slug: "test-3-astor-mirage-ukraine", title: "Макрон: Франция поставит Украине ракеты Aster и истребители Mirage", summary: "Политические заявления недели — в одной новости.", source: { name: "rt.com", slug: "rt" }, category: { name: "Политика", slug: "politika" }, url: "#", image: null, published_at: new Date().toISOString() },
  { id: 10004, slug: "test-4-parkovka-krysha", title: "На вокзале Петербурга крыша парковки рухнула на платформу", summary: "Инцидент без пострадавших, ведётся проверка.", source: { name: "rg.ru", slug: "rg" }, category: { name: "Происшествия", slug: "proisshestviya" }, url: "#", image: null, published_at: new Date().toISOString() },
  { id: 10005, slug: "test-5-kpr-modernizacia-teploseti", title: "КНР получит 1 млрд ₽ на модернизацию теплосетей", summary: "Финансирование направят в 2025–2026 годах.", source: { name: "tass.ru", slug: "tass" }, category: { name: "Экономика", slug: "ekonomika" }, url: "#", image: null, published_at: new Date().toISOString() },
  { id: 10006, slug: "test-6-gorky-park", title: "Золотая осень в Москве: кадры из Парка Горького", summary: "Фотопрогулка по городу: пока листья не улетели.", source: { name: "izotovlife", slug: "izotovlife" }, category: { name: "Без категории", slug: "bez-kategorii" }, url: "#", image: null, published_at: new Date().toISOString() },
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

/* ---------------- JWT УТИЛИТЫ ---------------- */
function parseJwt(token) {
  try {
    const [, payload] = token.split(".");
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json);
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
  try { localStorage.removeItem("access"); } catch {}
  delete api.defaults.headers.common["Authorization"];
}
export function setToken(token) {
  if (token && isJwtValid(token)) {
    try { localStorage.setItem("access", token); } catch {}
    applyAuthHeader(token);
  } else {
    dropToken();
  }
}
try {
  const saved = localStorage.getItem("access");
  if (saved && isJwtValid(saved)) applyAuthHeader(saved); else dropToken();
} catch {}

/* ---------------- ОБЩИЕ УТИЛИТЫ ---------------- */
export function normalizeSlug(raw) {
  if (!raw) return raw;
  let v = String(raw).trim();
  try { v = decodeURIComponent(v); } catch {}
  v = v.replace(/[?#].*$/g, "").replace(/-{2,}/g, "-").replace(/[-/]+$/g, "");
  return v.trim();
}
export function slugCandidates(raw) {
  if (!raw) return [];
  const t = String(raw).trim().replace(/[-/]+$/g, "");
  const norm = normalizeSlug(t);
  return Array.from(new Set([norm, t])).filter(Boolean);
}

// Прямые и обратные алиасы (канон → старые формы)
const SLUG_ALIASES = {
  obschestvo: "obshchestvo",
  "lenta-novostej": "lenta-novostey",
  proisshestvija: "proisshestviya",
};
const SLUG_BACK = {
  obshchestvo: ["obschestvo"],
  "lenta-novostey": ["lenta-novostej"],
  proisshestviya: ["proisshestvija"],
};
export function canonSlug(slug) {
  const s = normalizeSlug(slug);
  return SLUG_ALIASES[s] || s;
}
function backAliases(slug) {
  const s = canonSlug(slug);
  return SLUG_BACK[s] ? [s, ...SLUG_BACK[s]] : [s];
}

/** attachSeoUrl(obj)
 * Добавляет поле seo_url для удобной навигации на фронте.
 * Ничего не ломает, работает идемпотентно.
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
    if (obj.slug) {
  obj.seo_url = `${base}/${obj.slug}/`;
} else if (obj.title) {
  obj.seo_url = `${base}/${encodeURIComponent(
    String(obj.title).toLowerCase().replace(/\s+/g, "-")
  )}/`;
}
  } catch {}
  return obj;
}

/* ---------------- ПЛЕЙСХОЛДЕР И РЕСАЙЗЕР ---------------- */
export const DEFAULT_NEWS_PLACEHOLDER = (() => {
  const svg =
    `<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='630' viewBox='0 0 1200 630'>` +
    `<rect width='1200' height='630' fill='#20242c'/>` +
    `<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='Arial,Helvetica,sans-serif' font-size='48' fill='#f6f7fb'>IZOTOVLIFE</text>` +
    `</svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
})();
const AUDIO_EXT = [".mp3", ".ogg", ".wav", ".m4a", ".aac", ".flac"];
export function isAudioUrl(url) {
  if (!url) return false;
  const u = String(url).toLowerCase().split("?")[0];
  return AUDIO_EXT.some((ext) => u.endsWith(ext));
}
function isHttpLike(url) { return /^https?:\/\//i.test(String(url)); }
function isDataOrBlob(url) { return /^(data:|blob:|about:)/i.test(String(url || "")); }

// ⚙️ Обновлено: поддержка относительных путей к медиа с Django (/media/...)
export function buildThumbnailUrl(
  src,
  { w = 640, h = 360, q = 82, fmt = "webp", fit = "cover" } = {}
) {
  if (!src) return null;
  if (isAudioUrl(src)) return null;
  if (isDataOrBlob(src)) return src;

  // База сайта без /api на конце
  const DJ_BASE = API_BASE.replace(/\/api\/?$/, "");

  let absoluteSrc = String(src);

  if (isHttpLike(absoluteSrc)) {
    // ok
  } else if (/^\/?media\//i.test(absoluteSrc)) {
    absoluteSrc = `${DJ_BASE}/${absoluteSrc.replace(/^\/+/, "")}`;
  } else {
    return absoluteSrc;
  }

  const base = `${API_BASE}/media/thumbnail/`;
  const params = new URLSearchParams({
    src: absoluteSrc,
    w: String(w),
    h: String(h),
    q: String(q),
    fmt,
    fit,
  });
  return `${base}?${params.toString()}`;
}

export const buildThumb = buildThumbnailUrl;

export function buildThumbnailOrPlaceholder(url, opts) {
  const u = String(url || "");
  if (!u) return DEFAULT_NEWS_PLACEHOLDER;
  const built = buildThumbnailUrl(u, opts);
  return built || DEFAULT_NEWS_PLACEHOLDER;
}

/* ---------------- ТИХИЕ tryGet / tryPost ---------------- */
const QUIET_STATUSES = new Set([400, 401, 404, 405]);
const DEBUG_API = (() => { try { return localStorage.getItem("debugApi") === "1"; } catch { return false; } })();

export async function tryGet(paths, config = {}) {
  const list = typeof paths === "string" ? [paths] : Array.isArray(paths) ? paths : [];
  let lastErr = null;
  for (const p of list) {
    try { return await api.get(p, config); }
    catch (e) {
      const st = e?.response?.status;
      if (DEBUG_API) console.warn("tryGet fail:", p, st || e?.message);
      if (QUIET_STATUSES.has(st)) { lastErr = e; continue; }
      throw e;
    }
  }
  if (lastErr) throw lastErr;
  throw new Error("Все варианты путей вернули ошибку");
}
export async function tryPost(paths, data = {}, config = {}) {
  const list = typeof paths === "string" ? [paths] : Array.isArray(paths) ? paths : [];
  let lastErr = null;
  for (const p of list) {
    try { return await api.post(p, data, config); }
    catch (e) {
      const st = e?.response?.status;
      if (DEBUG_API) console.warn("tryPost fail:", p, st || e?.message);
      if (QUIET_STATUSES.has(st)) { lastErr = e; continue; }
      throw e;
    }
  }
  if (lastErr) throw lastErr;
  throw new Error("Все варианты POST-путей вернули ошибку");
}

/* ---------------- УМНЫЙ REQUEST-ИНТЕРСЕПТОР AXIOS ---------------- */
function _absUrlFromConfig(cfg) {
  const base = (cfg?.baseURL || API_BASE).replace(/\/+$/, "");
  const url = String(cfg?.url || "");
  if (/^https?:\/\//i.test(url)) return url;
  if (url.startsWith("/")) return `${base}${url}`;
  return `${base}/${url}`;
}
function _isEmptyRelatedUrl(u) {
  try {
    const x = new URL(u);
    const path = x.pathname.replace(/\/+$/, "/");
    return /\/api\/news\/related\/$/i.test(path) && !x.searchParams.has("slug");
  } catch { return false; }
}
function _noToken() {
  try { return !localStorage.getItem("access"); } catch { return true; }
}
function _localOkResponseAdapter(data, cfg) {
  return async () => ({ data, status: 200, statusText: "OK", headers: { "x-local": "1" }, config: cfg, request: null });
}
function _rewriteCategoryUrlSmart(u) {
  try {
    const x = new URL(u);
    const path = x.pathname.replace(/\/+$/, "/");
    const qs = x.searchParams;

    // Не трогаем корректный related
    if (/\/api\/news\/related\/$/i.test(path)) return u;

    // --- Категории (как раньше) ---
    if (path.endsWith("/api/news/") && qs.has("category")) {
      const s = qs.get("category") || "";
      const [canon, legacy] = backAliases(s);
      const page = qs.get("page") || "1";
      const ps = qs.get("page_size") || qs.get("limit") || "20";
      if (legacy && legacy !== canon) {
        return `${API_BASE}/news/${encodeURIComponent(legacy)}/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
      }
      return `${API_BASE}/news/category/${encodeURIComponent(canon)}/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
    }
    const m1 = path.match(/\/api\/categories\/([^/]+)\/news\/$/i);
    if (m1) {
      const s = decodeURIComponent(m1[1]);
      const [canon, legacy] = backAliases(s);
      const page = qs.get("page") || "1";
      const ps = qs.get("page_size") || "20";
      if (legacy && legacy !== canon) {
        return `${API_BASE}/news/${encodeURIComponent(legacy)}/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
      }
      return `${API_BASE}/news/category/${encodeURIComponent(canon)}/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
    }
    const m2 = path.match(/\/api\/category\/([^/]+)\/$/i);
    if (m2) {
      const s = decodeURIComponent(m2[1]);
      const [canon, legacy] = backAliases(s);
      const page = qs.get("page") || "1";
      const ps = qs.get("page_size") || qs.get("limit") || "20";
      if (legacy && legacy !== canon) {
        return `${API_BASE}/news/${encodeURIComponent(legacy)}/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
      }
      return `${API_BASE}/news/category/${encodeURIComponent(canon)}/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
    }
    const m3 = path.match(/\/api\/news\/category\/([^/]+)\/$/i);
    if (m3) {
      const s = decodeURIComponent(m3[1]);
      const [canon, legacy] = backAliases(s);
      if (legacy && legacy !== canon) {
        const page = qs.get("page") || "1";
        const ps = qs.get("page_size") || "20";
        return `${API_BASE}/news/${encodeURIComponent(legacy)}/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
      }
      return u;
    }

    // --- Страховки и устаревшие пути ---
    // 1) /api/news/news/ → /api/news/category/news/
    if (/\/api\/news\/news\/$/i.test(path)) {
      const page = qs.get("page") || "1";
      const ps = qs.get("page_size") || qs.get("limit") || "20";
      return `${API_BASE}/news/category/news/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
    }

    // 2) /api/news/check[/<slug>]/ → /api/news/favorites/check/?slug=...
    if (/\/api\/news\/check\/?$/i.test(path)) {
      const slug = qs.get("slug") || "";
      return slug
        ? `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`
        : `${API_BASE}/news/favorites/check/`;
    }
    const mChkNews = path.match(/\/api\/news\/check\/([^/]+)\/?$/i);
    if (mChkNews) {
      const slug = decodeURIComponent(mChkNews[1]);
      return `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`;
    }

    // 3) /api/favorites/check[/<slug>]/ → /api/news/favorites/check/?slug=...
    if (/\/api\/favorites\/check\/?$/i.test(path)) {
      const slug = qs.get("slug") || "";
      return slug
        ? `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`
        : `${API_BASE}/news/favorites/check/`;
    }
    const mChk = path.match(/\/api\/favorites\/check\/([^/]+)\/?$/i);
    if (mChk) {
      const slug = decodeURIComponent(mChk[1]);
      return `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`;
    }

    // 4) /api/news/favorites/check/<slug>/ → query
    const mNFChk = path.match(/\/api\/news\/favorites\/check\/([^/]+)\/?$/i);
    if (mNFChk) {
      const slug = decodeURIComponent(mNFChk[1]);
      return `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`;
    }

    // 5) toggle → всегда query-форма
    if (/\/api\/favorites\/toggle\/?$/i.test(path)) {
      const slug = qs.get("slug");
      return slug
        ? `${API_BASE}/news/favorites/toggle/?slug=${encodeURIComponent(slug)}`
        : `${API_BASE}/news/favorites/toggle/`;
    }
    const mTgl = path.match(/\/api\/favorites\/toggle\/([^/]+)\/?$/i);
    if (mTgl) {
      const slug = decodeURIComponent(mTgl[1]);
      return `${API_BASE}/news/favorites/toggle/?slug=${encodeURIComponent(slug)}`;
    }
    const mNFTgl = path.match(/\/api\/news\/favorites\/toggle\/([^/]+)\/?$/i);
    if (mNFTgl) {
      const slug = decodeURIComponent(mNFTgl[1]);
      return `${API_BASE}/news/favorites/toggle/?slug=${encodeURIComponent(slug)}`;
    }

    return u;
  } catch {
    return u;
  }
}

api.interceptors.request.use(
  (config) => {
    const abs = _absUrlFromConfig(config);

    // 👇 Если отправляем FormData, убираем принудительный JSON Content-Type
    const isFD = (typeof FormData !== "undefined") && (config?.data instanceof FormData);
    if (isFD && config.headers) {
      if (config.headers["Content-Type"]) delete config.headers["Content-Type"];
      if (config.headers["content-type"]) delete config.headers["content-type"];
    }

    if (_isEmptyRelatedUrl(abs)) {
      config.adapter = _localOkResponseAdapter([], config);
      return config;
    }

    if (_noToken()) {
      if (/\/api\/auth\/whoami\/$/i.test(abs) || /\/api\/users\/me\/$/i.test(abs)) {
        config.adapter = _localOkResponseAdapter({ is_authenticated: false, user: null }, config);
        return config;
      }
      if (/\/api\/news\/favorites\/check\/?/i.test(abs) || /\/api\/favorites\/check\/?/i.test(abs) || /\/api\/news\/check\/?/i.test(abs)) {
        config.adapter = _localOkResponseAdapter({ is_favorite: false }, config);
        return config;
      }
      if (/\/api\/news\/favorites\/(toggle|)$/i.test(abs) || /\/api\/favorites\/toggle\/?/i.test(abs)) {
        config.adapter = _localOkResponseAdapter({ is_favorite: false }, config);
        return config;
      }
    }

    const rewritten = _rewriteCategoryUrlSmart(abs);
    if (rewritten !== abs) {
      config.baseURL = "";
      config.url = rewritten;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Перелогин при 401 (без циклов)
api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const status = err?.response?.status;
    const config = err?.config || {};
    if (status === 401 && !config._retry) {
      dropToken();
      config._retry = true;
      if (config.headers) { delete config.headers["Authorization"]; delete config.headers.authorization; }
      try { return await api.request(config); } catch (e) { return Promise.reject(e); }
    }
    return Promise.reject(err);
  }
);

/* ---------------- ЛЕНТА ---------------- */
export async function fetchNews(page = 1, page_size = 20) {
  if (shouldUseFakeFeed()) return paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
  try {
    const r = await tryGet(["/news/feed/", "/news/"], { params: { page, page_size } });
    let data = [];
    if (Array.isArray(r.data)) data = r.data;
    else if (Array.isArray(r.data.results)) data = r.data.results;
    else if (r.data.results && typeof r.data.results === "object") data = Object.values(r.data.results);
    else if (Array.isArray(r.data.items)) data = r.data.items;
    else if (r.data?.results?.results) data = r.data.results.results;
    if (!Array.isArray(data) || data.length === 0) return paginate(TEST_FEED, page, page_size).map(attachSeoUrl);
    return data.map((n) => attachSeoUrl(n));
  } catch {
    return paginate(TEST_FEED, page, page_size).map((n) => attachSeoUrl(n));
  }
}

export async function fetchNewsFeedText({ page = 1, page_size = 30 } = {}) {
  if (shouldUseFakeFeed()) {
    const results = paginate(TEST_FEED, page, page_size).map(attachSeoUrl);
    return { count: TEST_FEED.length, next: null, previous: null, results };
  }
  try {
    const r = await api.get("/news/feed/text/", { params: { page, page_size } });
    const data =
      (Array.isArray(r.data?.results) && r.data.results) ||
      (Array.isArray(r.data) && r.data) ||
      (Array.isArray(r.data?.items) && r.data.items) || [];
    if (!data.length) {
      const results = paginate(TEST_FEED, page, page_size).map(attachSeoUrl);
      return { count: TEST_FEED.length, next: null, previous: null, results };
    }
    return { count: data.length, next: null, previous: null, results: data.map(attachSeoUrl) };
  } catch {
    const results = paginate(TEST_FEED, page, page_size).map(attachSeoUrl);
    return { count: TEST_FEED.length, next: null, previous: null, results };
  }
}

export async function fetchNewsFeedImages({ page = 1, page_size = 20 } = {}) {
  if (shouldUseFakeFeed()) {
    const results = paginate(TEST_FEED, page, page_size).map(attachSeoUrl);
    return { count: TEST_FEED.length, next: null, previous: null, results };
  }
  try {
    const r = await api.get("/news/feed/images/", { params: { page, page_size } });
    const data =
      (Array.isArray(r.data?.results) && r.data.results) ||
      (Array.isArray(r.data) && r.data) ||
      (Array.isArray(r.data?.items) && r.data.items) || [];
    if (!data.length) {
      const results = paginate(TEST_FEED, page, page_size).map(attachSeoUrl);
      return { count: TEST_FEED.length, next: null, previous: null, results };
    }
    return { count: data.length, next: null, previous: null, results: data.map(attachSeoUrl) };
  } catch {
    const results = paginate(TEST_FEED, page, page_size).map(attachSeoUrl);
    return { count: TEST_FEED.length, next: null, previous: null, results };
  }
}

/* ---------------- КАТЕГОРИИ ---------------- */
export async function fetchCategories() {
  try {
    const r = await tryGet(["/categories/", "/news/categories/", "/news/category-list/"]);
    const data = r.data;
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.results)) return data.results;
    if (data && typeof data === "object" && data.results) return Array.isArray(data.results) ? data.results : Object.values(data.results);
    if (DEBUG_API) console.warn("fetchCategories: неожиданный формат", data);
    return [];
  } catch { return []; }
}

export async function fetchCategoryCovers() {
  try {
    const r = await api.get("/categories/covers/");
    const data = r.data;
    if (Array.isArray(data)) { const m = {}; for (const x of data) if (x && x.slug) m[x.slug] = x.image || ""; return m; }
    if (data && typeof data === "object") return data;
    return {};
  } catch { return {}; }
}

export async function fetchFirstImageForCategory(slug) {
  if (!slug) return null;
  const s = canonSlug(slug);
  try {
    const r = await api.get("/news/feed/images/", { params: { category: s, limit: 1 } });
    const raw = r.data?.items || r.data?.results || (Array.isArray(r.data) ? r.data : []);
    const first = Array.isArray(raw) ? raw[0] : null;
    if (!first) return null;
    const src = first.image || first.cover_image || first.cover || first.image_url || first.thumbnail || null;
    return src || null;
  } catch { return null; }
}

/* ---------- ПРЕДОХРАНИТЕЛЬ ПО КАТЕГОРИЯМ ---------- */
const CAT_STOP_KEY = "CAT_STOP_AFTER_V1";
function _readCatStop() { try { const raw = sessionStorage.getItem(CAT_STOP_KEY); return raw ? JSON.parse(raw) : {}; } catch { return {}; } }
function _writeCatStop(map) { try { sessionStorage.setItem(CAT_STOP_KEY, JSON.stringify(map)); } catch {} }
let CAT_STOP_AFTER = _readCatStop();
function getCatStop(slug) { const s = canonSlug(slug); return Number(CAT_STOP_AFTER[s] || 0); }
function setCatStop(slug, pageNum) { const s = canonSlug(slug); const prev = Number(CAT_STOP_AFTER[s] || 0); if (pageNum > prev) { CAT_STOP_AFTER[s] = pageNum; _writeCatStop(CAT_STOP_AFTER); } }

/**
 * fetchCategoryNews(slug, opts)
 * Перебираем: path-ручки → квери-ручки. На пустых страницах помечаем stopAfter.
 * ❗️Редкий кейс удаления кандидата для слага 'news': избегаем /api/news/news/?...
 */
export async function fetchCategoryNews(slug, opts = 1) {
  if (!slug) return [];
  const page = typeof opts === "number" ? opts : Number(opts?.page || 1);
  const limitIn = typeof opts === "object" && opts?.limit ? Number(opts.limit) : undefined;
  const limit = limitIn ?? 20;

  const s = canonSlug(slug);
  const enc = encodeURIComponent(s);

  const stopAfter = getCatStop(s);
  if (stopAfter && page > stopAfter) return [];

  const unpack = (data) => {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.results)) return data.results;
    if (Array.isArray(data?.items)) return data.items;
    if (data?.results?.results && Array.isArray(data.results.results)) return data.results.results;
    if (data && typeof data === "object") { const vals = Object.values(data); if (vals.length && Array.isArray(vals[0])) return vals[0]; }
    return [];
  };

  if (shouldUseFakeFeed()) {
    const filtered = TEST_FEED.filter((i) => (i.category?.slug || "").toLowerCase() === s.toLowerCase());
    const arr = filtered.length ? filtered : TEST_FEED;
    const paged = paginate(arr, page, limit).map(attachSeoUrl);
    if (paged.length < limit) setCatStop(s, page);
    return paged;
  }

  // A) Путь-ручки (кандидат /news/<enc>/ пропускаем, если enc === 'news', чтобы не бить в /news/news/)
  const pathCandidates = [
    { path: `/news/category/${enc}/`, params: { page, limit, page_size: limit } },
    { path: `/category/${enc}/`, params: { page, limit, page_size: limit } },
    ...(s !== "news" ? [{ path: `/news/${enc}/`, params: { page, limit, page_size: limit } }] : []),
    { path: `/categories/${enc}/news/`, params: { page, page_size: limit } },
  ];
  for (const c of pathCandidates) {
    try {
      const r = await api.get(c.path, { params: c.params });
      const list = unpack(r.data);
      if (!Array.isArray(list) || list.length === 0) continue;
      const asked = Number(c.params?.page_size || c.params?.limit || limit);
      if (list.length < asked) setCatStop(s, page);
      return list.map(attachSeoUrl);
    } catch {}
  }

  // B) Квери-ручки
  const queryCandidates = [
    { path: "/news/feed/", params: { category: s, page, page_size: limit, limit } },
    { path: "/news/", params: { category: s, page, page_size: limit } },
    { path: "/news/", params: { category: s, page, limit } },
  ];
  let tried = false;
  for (const c of queryCandidates) {
    try {
      tried = true;
      const r = await api.get(c.path, { params: c.params });
      const list = unpack(r.data);
      if (!Array.isArray(list) || list.length === 0) continue;
      const asked = Number(c.params?.page_size || c.params?.limit || limit);
      if (list.length < asked) setCatStop(s, page);
      return list.map(attachSeoUrl);
    } catch {}
  }
  if (tried) setCatStop(s, page);

  const filtered = TEST_FEED.filter((i) => (i.category?.slug || "").toLowerCase() === s.toLowerCase());
  const arr = filtered.length ? filtered : TEST_FEED;
  const paged = paginate(arr, page, limit).map(attachSeoUrl);
  if (paged.length < limit) setCatStop(s, page);
  return paged;
}

/* ---------------- ПОИСК ---------------- */
export async function searchAll(query, { limit = 30, offset = 0 } = {}) {
  if (!query) return { items: [], total: 0 };
  try {
    const r = await api.get("/news/search/", { params: { q: query, limit, offset } });
    const items = r.data.results || r.data.items || [];
    return { items: items.map(attachSeoUrl), total: r.data.count ?? items.length };
  } catch { return { items: [], total: 0 }; }
}
export async function fetchSmartSearch(query) {
  if (!query || query.length < 2) return [];
  try {
    const r = await api.get("/news/search/smart/", { params: { q: query }, timeout: 5000 });
    const results = Array.isArray(r.data?.results) ? r.data.results : Array.isArray(r.data) ? r.data : [];
    return results.map(attachSeoUrl);
  } catch { return []; }
}

/* ---------------- РЕЗОЛВЕР И СТАТЬИ ---------------- */
export async function resolveNews(slug) {
  if (!slug) throw new Error("resolveNews: пустой slug");
  const norm = normalizeSlug(slug);
  const r = await tryGet([
    `/news/resolve/${encodeURIComponent(norm)}/`,
    `/news/by-slug/${encodeURIComponent(norm)}/`,
  ]);
  return r.data;
}
export { resolveNews as resolveNewsApi };

export async function fetchArticle(arg1, arg2) {
  let category = null, slug = null;
  if (typeof arg1 === "string" && typeof arg2 !== "string") slug = arg1;
  else if (typeof arg1 === "object" && arg1 !== null) { category = arg1.category || null; slug = arg1.slug || arg1.seo_slug || arg1.url_slug || null; }
  else { category = arg1 || null; slug = arg2 || null; }
  if (!slug) throw new Error("fetchArticle: нужен slug");
  const cands = slugCandidates(slug);

  try {
    const resolved = await resolveNews(cands[0] || slug);
    const detail = resolved?.detail_url;
    if (detail) { const r = await api.get(detail); return attachSeoUrl(r.data, "article"); }
  } catch {}

  const directPaths = [
    ...cands.map((s) => `/news/${encodeURIComponent(s)}/`),
    ...cands.map((s) => `/article/${encodeURIComponent(s)}/`),
  ];
  if (category) {
    const cat = encodeURIComponent(String(category));
    for (const s of cands) {
      directPaths.push(`/news/${cat}/${encodeURIComponent(s)}/`);
      directPaths.push(`/news/article/${cat}/${encodeURIComponent(s)}/`);
    }
  }
  const r = await tryGet(directPaths);
  return attachSeoUrl(r.data, "article");
}

export async function fetchImportedNews(source, slug) {
  if (!source || !slug) throw new Error("fetchImportedNews: нужен source && slug");
  const cands = slugCandidates(slug);
  const r = await tryGet(cands.map((s) => `/news/rss/${encodeURIComponent(source)}/${encodeURIComponent(s)}/`));
  return attachSeoUrl(r.data, "rss");
}

/* ---------------- ПОХОЖИЕ НОВОСТИ ---------------- */
export async function fetchRelated(...args) {
  let slug = null, limit = 6;
  if (args.length === 1 && typeof args[0] === "object" && args[0] !== null) { slug = args[0].slug; if (args[0].limit != null) limit = args[0].limit; }
  else if (args.length >= 1 && typeof args[0] === "string") { slug = args[0]; if (typeof args[1] === "number") limit = args[1]; }
  let legacy = null;
  if (!slug && args.length >= 3) { const [, param, legacySlug] = args; legacy = { param, slug: legacySlug }; slug = legacySlug; }
  if (!slug) return []; // не дергаем сеть

  const cands = slugCandidates(slug);
  const pathsPref = [
    ...cands.map((s) => `/news/${encodeURIComponent(s)}/related/`),
    ...cands.map((s) => `/news/related/${encodeURIComponent(s)}/`),
    "/news/related/",
  ];
  try {
    const r = await tryGet(pathsPref, { params: { slug: cands[0], limit } });
    const data = r.data?.results || r.data || [];
    return Array.isArray(data) ? data.map(attachSeoUrl) : data;
  } catch {}

  if (legacy && legacy.param) {
    const rssPaths = cands.map((s) => `/news/rss/${encodeURIComponent(legacy.param)}/${encodeURIComponent(s)}/related/`);
    const articlePaths = cands.map((s) => `/news/article/${encodeURIComponent(legacy.param)}/${encodeURIComponent(s)}/related/`);
    const universalPaths = cands.map((s) => `/news/${encodeURIComponent(legacy.param)}/${encodeURIComponent(s)}/related/`);
    const r2 = await tryGet([...articlePaths, ...rssPaths, ...universalPaths], { params: { limit } });
    const data2 = r2.data?.results || r2.data || [];
    return Array.isArray(data2) ? data2.map(attachSeoUrl) : data2;
  }
  return [];
}

/* ---------------- ИЗБРАННОЕ ---------------- */
function _hasToken() { try { return !!localStorage.getItem("access"); } catch { return false; } }
export async function favoritesCheck(slug) {
  if (!slug) return false;
  if (!_hasToken()) return false;
  try {
    const r = await tryGet(
      [
        `/news/favorites/${encodeURIComponent(slug)}/check/`,
        `/news/favorites/check/${encodeURIComponent(slug)}/`,
        `/news/favorites/check/`,
        // совместимость со старыми путями без префикса /news/
        `/favorites/${encodeURIComponent(slug)}/check/`,
        `/favorites/check/${encodeURIComponent(slug)}/`,
        `/favorites/check/`,
        // совсем старое
        `/news/check/`,
      ],
      { params: { slug } }
    );
    return !!(r.data && (r.data.is_favorite || r.data.favorite));
  } catch (e) { if (e?.response?.status === 401) return false; return false; }
}
export async function favoritesToggle(slug) {
  if (!slug) return { is_favorite: false };
  if (!_hasToken()) return { is_favorite: false };
  try {
    const r = await tryPost(
      [
        `/news/favorites/${encodeURIComponent(slug)}/toggle/`,
        "/news/favorites/toggle/",
        "/news/favorites/",
        // совместимость
        `/favorites/${encodeURIComponent(slug)}/toggle/`,
        "/favorites/toggle/",
        "/favorites/",
      ],
      { slug }
    );
    return r.data || { is_favorite: false };
  } catch (e) { if (e?.response?.status === 401) return { is_favorite: false }; throw e; }
}

/* ---------------- МЕТРИКИ ---------------- */
export async function hitMetrics(type, slug) {
  try {
    const normType = type === "a" ? "article" : type === "i" ? "rss" : type;
    const cands = slugCandidates(slug);
    const s = cands[0] || normalizeSlug(slug);
    const r = await api.post("/news/metrics/hit/", { type: normType, slug: s });
    return r.data;
  } catch (e) { const st = e?.response?.status; if (st !== 404 && DEBUG_API) console.warn("metrics/hit warn:", st || e?.message); return null; }
}

/* ---------------- СТРАНИЦЫ ---------------- */
export async function fetchPages() { try { const r = await api.get("/pages/"); return r.data; } catch { return []; } }
export async function fetchPage(slug) { try { const r = await api.get(`/pages/${slug}/`); return r.data; } catch { return null; } }

/* ---------------- ПРЕДЛОЖИТЬ НОВОСТЬ ---------------- */
export async function suggestNews(payload) {
  try {
    // Если уже передали FormData — просто отправляем
    const isFD = (typeof FormData !== "undefined") && (payload instanceof FormData);
    if (isFD) {
      const r1 = await api.post("/news/suggest/", payload, { timeout: 15000 });
      return r1.data;
    }

    // Если прислали обычный объект — решим, нужен ли multipart
    const p = payload && typeof payload === "object" ? payload : {};
    const hasFile =
      (typeof File !== "undefined" && (p.image_file instanceof File || p.video_file instanceof File)) ||
      (p.image_file && typeof p.image_file === "object" && "size" in p.image_file) ||
      (p.video_file && typeof p.video_file === "object" && "size" in p.video_file);

    if (hasFile) {
      // Собираем FormData (дублируем ключи файлов под популярные имена)
      const fd = new FormData();
      const appendIf = (k, v) => { if (v != null && v !== "") fd.append(k, v); };

      appendIf("first_name", p.first_name);
      appendIf("last_name", p.last_name);
      appendIf("email", p.email);
      appendIf("phone", p.phone);
      appendIf("title", p.title);
      appendIf("message", p.message);
      appendIf("website", p.website); // honeypot

      if (p.image_file) {
        fd.append("image_file", p.image_file);
        fd.append("image", p.image_file);
        fd.append("photo", p.image_file);
      }
      if (p.video_file) {
        fd.append("video_file", p.video_file);
        fd.append("video", p.video_file);
      }

      // Токен капчи, если пришёл строкой в p.recaptcha
      if (typeof p.recaptcha === "string" && p.recaptcha.trim()) {
        fd.append("captcha", p.recaptcha);
        fd.append("recaptcha", p.recaptcha);
        fd.append("g-recaptcha-response", p.recaptcha);
      }

      const r2 = await api.post("/news/suggest/", fd, { timeout: 15000 });
      return r2.data;
    }

    // Иначе — обычный JSON без принудительного заголовка
    const body = { ...p };
    if (typeof p.recaptcha === "string" && p.recaptcha.trim() && !("captcha" in body) && !("g-recaptcha-response" in body)) {
      body.captcha = p.recaptcha;
      body["g-recaptcha-response"] = p.recaptcha;
    }
    const r3 = await api.post("/news/suggest/", body, { timeout: 15000 });
    return r3.data;
  } catch (e) {
    if (e.response?.data) throw e.response.data;
    throw new Error(e.message || "Network error");
  }
}

/* ---------------- АУТЕНТИФИКАЦИЯ ---------------- */
export async function login(username, password) {
  const body = { username, password };
  const r = await tryPost(["/auth/login/", "/auth/token/login/", "/auth/jwt/create/"], body);
  const token = r.data?.access || r.data?.auth_token || r.data?.key;
  if (token) setToken(token);
  return r.data;
}
export async function register(data) { const r = await api.post("/auth/register/", data); return r.data; }
export async function whoami() {
  const hasToken = !!localStorage.getItem("access");
  if (!hasToken) return null;
  try {
    const r = await tryGet(["/auth/me/", "/auth/whoami/", "/users/me/", "/auth/user/"]);
    return r.data;
  } catch (e) { if ([401, 403].includes(e?.response?.status)) return null; return null; }
}

/* ---------------- АВТОРСКИЕ СТАТЬИ ---------------- */
export async function fetchAuthorArticles(params = {}) { const r = await api.get("/author/articles/", { params }); return r.data; }
export async function fetchNewsArticles(params = {}) { return fetchAuthorArticles(params); }

/* ---------------- АДМИН-СЕССИЯ ---------------- */
export async function adminSessionLogin() { const r = await api.post("/security/admin-session-login/"); return r.data; }
export async function goToAdmin() {
  try {
    const r = await adminSessionLogin();
    let url = r.admin_url;
    if (url.startsWith("/")) {
      const base = api.defaults.baseURL.replace(/\/api$/, "");
      url = base + url;
    }
    window.location.href = url;
  } catch (err) { if (DEBUG_API) console.error("Не удалось открыть админку:", err); }
}

export default api;

/* ---------------- ГЛОБАЛЬНЫЙ ПАТЧ ДЛЯ window.fetch (браузер) ---------------- */
(function installGlobalFetchPatch() {
  if (typeof window === "undefined" || typeof window.fetch !== "function") return;
  const orig = window.fetch;

  const hasToken = () => { try { return !!localStorage.getItem("access"); } catch { return false; } };
  const abs = (u) => { try { return new URL(u, window.location.origin).toString(); } catch { return String(u || ""); } };

  function isEmptyRelated(u) {
    try {
      const x = new URL(u);
      const path = x.pathname.replace(/\/+$/, "/");
      return /\/api\/news\/related\/$/i.test(path) && !x.searchParams.has("slug");
    } catch {
      return false;
    }
  }

  // 👇 Переписываем устаревшие пути на рабочие (убираем 404 по favorites/check|toggle и news/check)
  function rewriteLegacy(u) {
    try {
      const x = new URL(u);
      const p = x.pathname.replace(/\/+$/, "/");
      const qs = x.searchParams;

      // /api/news/check[/<slug>]/ → /api/news/favorites/check/?slug=...
      if (/\/api\/news\/check\/?$/i.test(p)) {
        const slug = qs.get("slug") || "";
        return slug
          ? `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`
          : `${API_BASE}/news/favorites/check/`;
      }
      const mN = p.match(/\/api\/news\/check\/([^/]+)\/?$/i);
      if (mN) return `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(decodeURIComponent(mN[1]))}`;

      // /api/favorites/check[/<slug>]/ → /api/news/favorites/check/?slug=...
      if (/\/api\/favorites\/check\/?$/i.test(p)) {
        const slug = qs.get("slug") || "";
        return slug
          ? `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`
          : `${API_BASE}/news/favorites/check/`;
      }
      const mC = p.match(/\/api\/favorites\/check\/([^/]+)\/?$/i);
      if (mC) return `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(decodeURIComponent(mC[1]))}`;

      // /api/news/favorites/check/<slug>/ → query
      const mNC = p.match(/\/api\/news\/favorites\/check\/([^/]+)\/?$/i);
      if (mNC) return `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(decodeURIComponent(mNC[1]))}`;

      // toggle → query
      if (/\/api\/favorites\/toggle\/?$/i.test(p)) {
        const slug = qs.get("slug");
        return slug
          ? `${API_BASE}/news/favorites/toggle/?slug=${encodeURIComponent(slug)}`
          : `${API_BASE}/news/favorites/toggle/`;
      }
      const mT = p.match(/\/api\/favorites\/toggle\/([^/]+)\/?$/i);
      if (mT) return `${API_BASE}/news/favorites/toggle/?slug=${encodeURIComponent(decodeURIComponent(mT[1]))}`;
      const mNT = p.match(/\/api\/news\/favorites\/toggle\/([^/]+)\/?$/i);
      if (mNT) return `${API_BASE}/news/favorites/toggle/?slug=${encodeURIComponent(decodeURIComponent(mNT[1]))}`;

      // /api/news/news/ → безопасный слайс категории news
      if (/\/api\/news\/news\/$/i.test(p)) {
        const page = qs.get("page") || "1";
        const ps = qs.get("page_size") || qs.get("limit") || "20";
        return `${API_BASE}/news/category/news/?page=${encodeURIComponent(page)}&limit=${encodeURIComponent(ps)}&page_size=${encodeURIComponent(ps)}`;
      }

      return u;
    } catch {
      return u;
    }
  }

  window.fetch = async function patchedFetch(input, init = {}) {
    const url0 = abs(typeof input === "string" ? input : input?.url || "");

    // Пустой related без slug — сразу отдаём []
    if (isEmptyRelated(url0)) {
      return new Response(JSON.stringify([]), {
        status: 200,
        headers: { "Content-Type": "application/json", "x-local": "1" }
      });
    }

    // Перепишем легаси-адреса, чтобы не ловить 404
    const url = rewriteLegacy(url0);

    // Для гостей мгновенно отвечаем "не в избранном"
    if (!hasToken()) {
      if (/\/api\/news\/favorites\/check\/?/i.test(url)) {
        return new Response(JSON.stringify({ is_favorite: false }), {
          status: 200, headers: { "Content-Type": "application/json", "x-local": "1" }
        });
      }
      if (/\/api\/news\/favorites\/(toggle|)$/i.test(url)) {
        return new Response(JSON.stringify({ is_favorite: false }), {
          status: 200, headers: { "Content-Type": "application/json", "x-local": "1" }
        });
      }
    }

    // Если адрес переписали — шлём по новому
    if (url !== url0) return orig(url, init);

    // Иначе — как обычно
    return orig(input, init);
  };
})();
/* ---------------- ПАТЧ ДЛЯ <img> И СЫРОГО XHR (глушим /api/news/check/) ---------------- */
(function installLegacyCheckGuards() {
  if (typeof window === "undefined") return;

  function rewriteLegacy(u) {
    try {
      const x = new URL(String(u), window.location.origin);
      const p = x.pathname.replace(/\/+$/, "/");
      const qs = x.searchParams;

      // /api/news/check[/<slug>]/ → /api/news/favorites/check/?slug=...
      if (/\/api\/news\/check\/?$/i.test(p)) {
        const slug = qs.get("slug") || "";
        return slug
          ? `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`
          : `${API_BASE}/news/favorites/check/`;
      }
      const m = p.match(/\/api\/news\/check\/([^/]+)\/?$/i);
      if (m) {
        const slug = decodeURIComponent(m[1]);
        return `${API_BASE}/news/favorites/check/?slug=${encodeURIComponent(slug)}`;
      }
    } catch {}
    return String(u || "");
  }

  // 2.1 Патчим <img src="...">
  try {
    const desc = Object.getOwnPropertyDescriptor(Image.prototype, "src");
    if (desc && desc.set) {
      Object.defineProperty(Image.prototype, "src", {
        get: function () { return desc.get.call(this); },
        set: function (v) { desc.set.call(this, rewriteLegacy(v)); },
        configurable: true,
        enumerable: true,
      });
    }
  } catch {}

  // 2.2 Патчим «сырой» XMLHttpRequest
  try {
    const origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
      return origOpen.call(this, method, rewriteLegacy(url), ...rest);
    };
  } catch {}
})();
