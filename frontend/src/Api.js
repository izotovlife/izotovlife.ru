// Путь: frontend/src/Api.js
// Назначение: Axios-инстанс и функции API (логин, регистрация, восстановление пароля,
// работа с новостями, категории, авторские и редакторские статьи, админ URL, SEO-маршруты).
// Обновлено (совместимость с backend/news/urls.py):
//   ✅ baseURL берём из config.API_BASE (без хардкода).
//   ✅ SEO RSS detail: /news/rss/<source_slug>/<slug>/ (БЕЗ лишнего сегмента "source").
//   ✅ Похожие: /news/related/<slug>/ (общий эндпоинт, не вложенный).
//   ✅ Метрики: /news/hit/<slug>/.
//   ✅ normalizeSlug НЕ режет хвостовой дефис (слуги вида '...-' поддержаны).
//   ✅ slugCandidates перебирает сырой/декодированный/триммированный/нормализованный варианты.
//   ✅ Функции fetchArticle(category, slug) и fetchImportedNews(source, slug) сохранены.
//   ✅ Добавлены безопасные fallback-варианты fetchArticleBySlug(slug) и fetchImportedBySlug(slug).

import axios from "axios";
import { API_BASE } from "./config";

// ---------------- БАЗОВАЯ НАСТРОЙКА ----------------

const api = axios.create({
  baseURL: API_BASE,
});

// ---------------- ВСПОМОГАТЕЛЬНОЕ ----------------

function normalizeSlug(raw) {
  if (!raw) return raw;
  let v = String(raw);
  try { v = decodeURIComponent(v); } catch {}
  v = v.trim();
  v = v.replace(/[?#].*$/g, ""); // убрать query/fragment
  v = v.replace(/-{2,}/g, "-");  // схлопнуть повторные дефисы
  // ВАЖНО: не обрезаем хвостовой дефис!
  return v;
}

function uniqueArray(arr) {
  const seen = new Set();
  const out = [];
  for (const x of arr) {
    const k = String(x);
    if (!seen.has(k)) {
      seen.add(k);
      out.push(x);
    }
  }
  return out;
}

function slugCandidates(raw) {
  if (!raw) return [];
  const rawStr = String(raw);
  let decoded = rawStr;
  try { decoded = decodeURIComponent(rawStr); } catch {}
  const rawTrim = decoded.trim();
  const norm = normalizeSlug(rawTrim);
  return uniqueArray([rawStr, decoded, rawTrim, norm].filter(Boolean));
}

async function tryGet(paths, config) {
  let lastErr;
  for (const p of paths) {
    try {
      const r = await api.get(p, config);
      return r;
    } catch (e) {
      lastErr = e;
    }
  }
  if (lastErr) throw lastErr;
  throw new Error("No endpoints succeeded");
}

function attachSeoUrl(obj, type) {
  if (!obj || obj.seo_url) return obj;
  if (type === "article" || obj.categories) {
    obj.seo_url = `/news/${obj.categories?.[0]?.slug || "news"}/${obj.slug}`;
  } else if (type === "rss" || obj.source) {
    obj.seo_url = `/news/source/${obj.source?.slug || "source"}/${obj.slug}`;
  }
  return obj;
}

// ---------------- JWT ----------------

export function setToken(token) {
  if (token) {
    localStorage.setItem("access", token);
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    localStorage.removeItem("access");
    delete api.defaults.headers.common["Authorization"];
  }
}

const saved = localStorage.getItem("access");
if (saved) {
  api.defaults.headers.common["Authorization"] = `Bearer ${saved}`;
}

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem("access");
      delete api.defaults.headers.common["Authorization"];
    }
    return Promise.reject(err);
  }
);

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
  const token = localStorage.getItem("access");
  if (!token) return null;
  try {
    const r = await api.get("/auth/me/");
    return r.data;
  } catch (err) {
    if (err?.response?.status === 401) return null;
    throw err;
  }
}

// ---------------- ВОССТАНОВЛЕНИЕ ПАРОЛЯ ----------------

export async function requestPasswordReset(data) {
  const r = await api.post("/auth/password-reset/", data);
  return r.data;
}

export async function confirmPasswordReset(uid, token, data) {
  const r = await api.post(`/auth/password-reset-confirm/${uid}/${token}/`, data);
  return r.data;
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
    console.error("Не удалось получить admin_url", err);
  }
}

// ---------------- ЛЕНТА ----------------

export async function fetchNews(page = 1) {
  try {
    const r = await api.get("/news/feed/", { params: { page } });
    if (r.data && typeof r.data === "object" && Array.isArray(r.data.results)) {
      r.data.results = r.data.results.map((n) => attachSeoUrl(n));
      return r.data;
    }
    if (Array.isArray(r.data)) {
      return { results: r.data.map((n) => attachSeoUrl(n)), count: r.data.length };
    }
    return { results: [], count: 0 };
  } catch (err) {
    console.error("Ошибка API fetchNews:", err);
    return { results: [], count: 0 };
  }
}

export async function fetchPopular(page = 1, limit = 10) {
  const r = await api.get("/news/feed/", {
    params: { page, ordering: "-views_count", limit },
  });
  const data = r.data?.results || r.data;
  return Array.isArray(data) ? data.map((n) => attachSeoUrl(n)) : data;
}

export async function fetchFeedText(page = 1) {
  const r = await api.get("/news/feed/text/", { params: { page } });
  return r.data;
}

export async function fetchFeedImages(page = 1) {
  const r = await api.get("/news/feed/images/", { params: { page } });
  return r.data;
}

// ---------------- КАТЕГОРИИ ----------------

export async function fetchCategories() {
  const r = await api.get("/news/categories/");
  return r.data;
}

export async function fetchCategoryNews(slug, page = 1) {
  const r = await api.get(`/news/category/${slug}/`, { params: { page } });
  const data = r.data?.results || r.data;
  return Array.isArray(data) ? data.map((n) => attachSeoUrl(n)) : data;
}

// ---------------- ПОИСК ----------------
// Универсальный парсер: поддерживает results, items и массив
export async function searchAll(query, { limit = 30, offset = 0 } = {}) {
  if (!query) return { results: [], count: 0 };
  try {
    const r = await api.get("/news/search/", {
      params: { q: query, limit, offset },
    });

    const data = r.data;
    let results = [];
    if (Array.isArray(data)) results = data;
    else if (Array.isArray(data.results)) results = data.results;
    else if (Array.isArray(data.items)) results = data.items;
    else if (data?.data && Array.isArray(data.data)) results = data.data;

    const count = data?.count ?? data?.total ?? results.length ?? 0;
    const enriched = results.map((n) => attachSeoUrl(n));
    return { results: enriched, count };
  } catch (err) {
    console.error("Ошибка поиска:", err);
    return { results: [], count: 0 };
  }
}

// ---------------- СТАТЬИ (DETAIL) ----------------
// SEO-вариант (основной): /news/article/<category_slug>/<slug>/
export async function fetchArticle(category, slug) {
  if (!category || !slug) throw new Error("fetchArticle: нужен category и slug");
  const cands = slugCandidates(slug);
  const paths = cands.map(
    (s) => `/news/article/${encodeURIComponent(category)}/${encodeURIComponent(s)}/`
  );
  // fallback (короткий detail, если включён на бэке): /news/article/<slug>/
  paths.push(
    ...cands.map((s) => `/news/article/${encodeURIComponent(s)}/`)
  );
  const r = await tryGet(paths);
  return attachSeoUrl(r.data, "article");
}

// Fallback-вариант по короткому пути (если открыли /news/:slug и ещё не знаем категорию)
export async function fetchArticleBySlug(slug) {
  const cands = slugCandidates(slug);
  const paths = cands.map((s) => `/news/article/${encodeURIComponent(s)}/`);
  const r = await tryGet(paths);
  return attachSeoUrl(r.data, "article");
}

// ---------------- ИМПОРТ (DETAIL) ----------------
// SEO-вариант (основной): /news/rss/<source_slug>/<slug>/
export async function fetchImportedNews(source, slug) {
  if (!source || !slug) throw new Error("fetchImportedNews: нужен source и slug");
  const cands = slugCandidates(slug);
  const paths = cands.map(
    (s) => `/news/rss/${encodeURIComponent(source)}/${encodeURIComponent(s)}/`
  );
  // fallback (короткий detail, если включён на бэке): /news/rss/<slug>/
  paths.push(
    ...cands.map((s) => `/news/rss/${encodeURIComponent(s)}/`)
  );
  const r = await tryGet(paths);
  return attachSeoUrl(r.data, "rss");
}

// Fallback-вариант по короткому пути
export async function fetchImportedBySlug(slug) {
  const cands = slugCandidates(slug);
  const paths = cands.map((s) => `/news/rss/${encodeURIComponent(s)}/`);
  const r = await tryGet(paths);
  return attachSeoUrl(r.data, "rss");
}

// Универсальный переключатель по типу (оставил для совместимости)
export async function fetchUniversalArticle(type, param, slug) {
  const normType = type === "a" ? "article" : type === "i" ? "rss" : type;
  if (normType === "article") return fetchArticle(param, slug);
  if (normType === "rss") return fetchImportedNews(param, slug);
  throw new Error("Unknown article type: " + type);
}

// ---------------- ПОХОЖИЕ НОВОСТИ ----------------
// Бэкенд-роут общий: /news/related/<slug>/
export async function fetchRelated(slug) {
  if (!slug) throw new Error("fetchRelated: нужен slug");
  const cands = slugCandidates(slug);
  const paths = cands.map((s) => `/news/related/${encodeURIComponent(s)}/`);
  const r = await tryGet(paths);
  const data = r.data?.results || r.data || [];
  return Array.isArray(data) ? data.map((n) => attachSeoUrl(n)) : data;
}

// ---------------- МЕТРИКИ ----------------
// Бэкенд-роут: /news/hit/<slug>/
export async function hitMetrics(slug) {
  try {
    const cands = slugCandidates(slug);
    const s = cands[0] || normalizeSlug(slug);
    const r = await api.post(`/news/hit/${encodeURIComponent(s)}/`);
    return r.data;
  } catch (err) {
    console.error("hit metrics error", err);
    return null;
  }
}

// ---------------- СТАТИЧЕСКИЕ СТРАНИЦЫ ----------------

export async function fetchPages() {
  const r = await api.get("/pages/");
  return r.data;
}

export async function fetchPage(slug) {
  const r = await api.get(`/pages/${slug}/`);
  return r.data;
}

// ---------------- РЕЗОЛВЕР SLUG ----------------

export async function resolveNews(slug) {
  if (!slug) throw new Error("resolveNews: пустой slug");
  const cands = slugCandidates(slug);
  const paths = cands.map((s) => `/news/resolve/${encodeURIComponent(s)}/`);
  const r = await tryGet(paths);
  return r.data; // ожидаем { type: "article"|"rss", slug, category_slug?, source_slug? }
}

export default api;
