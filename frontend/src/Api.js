// Путь: frontend/src/Api.js
// Назначение: Axios-инстанс и функции API (новости, категории, поиск, страницы, аутентификация, админ-доступ).
// Исправлено:
//   ✅ Полностью удалены упоминания источников из URL.
//   ✅ Детальная новость: /api/news/<slug>/
//   ✅ Похожие новости: /api/news/<slug>/related/
//   ✅ Категории: /api/category/<slug>/
//   ✅ Совместимо с backend/news/urls.py (новая структура без источников).

import axios from "axios";

// ---------------- БАЗОВАЯ НАСТРОЙКА ----------------
const api = axios.create({
  baseURL: "http://localhost:8000/api",
});

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
  return p?.exp && p.exp > Date.now() / 1000 + 5;
}

function dropToken() {
  try {
    localStorage.removeItem("access");
  } catch {}
  delete api.defaults.headers.common["Authorization"];
}

function applyAuthHeader(token) {
  api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

// ---------------- JWT ----------------
export function setToken(token) {
  if (token && isJwtValid(token)) {
    try {
      localStorage.setItem("access", token);
    } catch {}
    applyAuthHeader(token);
  } else dropToken();
}

let saved = null;
try {
  saved = localStorage.getItem("access");
} catch {}
if (saved && isJwtValid(saved)) applyAuthHeader(saved);
else dropToken();

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const status = err?.response?.status;
    const config = err?.config || {};
    if (status === 401) {
      dropToken();
      if (!config._retry) {
        config._retry = true;
        delete config.headers?.Authorization;
        try {
          return await api.request(config);
        } catch (e) {
          return Promise.reject(e);
        }
      }
    }
    return Promise.reject(err);
  }
);

// ---------------- ВСПОМОГАТЕЛЬНЫЕ ----------------
function normalizeSlug(raw) {
  if (!raw) return raw;
  let v = String(raw).trim();
  try {
    v = decodeURIComponent(v);
  } catch {}
  return v.replace(/[?#].*$/g, "").replace(/-{2,}/g, "-").replace(/[-/]+$/g, "").trim();
}

function slugCandidates(raw) {
  if (!raw) return [];
  const t = String(raw).trim().replace(/[-/]+$/g, "");
  const norm = normalizeSlug(t);
  return Array.from(new Set([norm, t])).filter(Boolean);
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
  throw lastErr || new Error("Все варианты путей вернули 404");
}

function attachSeoUrl(obj) {
  if (!obj || obj.seo_url) return obj;
  try {
    obj.seo_url = `/news/${obj.slug}/`;
  } catch (err) {
    console.warn("⚠️ attachSeoUrl: ошибка при формировании SEO URL", err);
  }
  return obj;
}

// ---------------- ЛЕНТА ----------------
export async function fetchNews(page = 1) {
  try {
    const r = await api.get("/news/feed/", { params: { page } });
    const data = r.data.results || r.data.items || r.data;
    return (Array.isArray(data) ? data : []).map(attachSeoUrl);
  } catch (err) {
    console.error("Ошибка загрузки новостей:", err);
    return [];
  }
}

// ---------------- КАТЕГОРИИ ----------------
export async function fetchCategories() {
  try {
    const r = await api.get("/categories/");
    const d = r.data;
    if (Array.isArray(d)) return d;
    if (Array.isArray(d.results)) return d.results;
    return d?.results ? Object.values(d.results) : [];
  } catch (err) {
    console.error("Ошибка загрузки категорий:", err);
    return [];
  }
}

// ---------------- НОВОСТИ КАТЕГОРИИ ----------------
export async function fetchCategoryNews(slug, page = 1) {
  if (!slug) return [];
  const encoded = encodeURIComponent(slug);
  const paths = [`/category/${encoded}/`, `/news/category/${encoded}/`];
  try {
    const r = await tryGet(paths, { params: { page } });
    const data = r.data.results || r.data.items || r.data;
    return (Array.isArray(data) ? data : []).map(attachSeoUrl);
  } catch (err) {
    console.error("Ошибка загрузки новостей категории:", err);
    return [];
  }
}

// ---------------- ПОИСК ----------------
export async function searchAll(q, { limit = 30, offset = 0 } = {}) {
  if (!q) return { items: [], total: 0 };
  try {
    const r = await api.get("/news/search/", { params: { q, limit, offset } });
    const items = r.data.results || r.data.items || [];
    return { items: items.map(attachSeoUrl), total: r.data.count ?? items.length };
  } catch (e) {
    console.error("Ошибка поиска:", e);
    return { items: [], total: 0 };
  }
}

// ---------------- ДЕТАЛЬНАЯ НОВОСТЬ ----------------
export async function fetchArticle(slug) {
  const cands = slugCandidates(slug);
  const paths = cands.map((s) => `/news/${encodeURIComponent(s)}/`);
  const r = await tryGet(paths);
  return attachSeoUrl(r.data);
}

// ---------------- ПОХОЖИЕ ----------------
export async function fetchRelated(slug) {
  const cands = slugCandidates(slug);
  const paths = cands.map((s) => `/news/${encodeURIComponent(s)}/related/`);
  try {
    const r = await tryGet(paths);
    const data = r.data?.results || r.data || [];
    return Array.isArray(data) ? data.map(attachSeoUrl) : data;
  } catch (err) {
    console.warn("fetchRelated error:", err);
    return [];
  }
}

// ---------------- МЕТРИКИ ----------------
export async function hitMetrics(slug) {
  try {
    const s = slugCandidates(slug)[0] || normalizeSlug(slug);
    const r = await api.post("/news/metrics/hit/", { slug: s });
    return r.data;
  } catch (e) {
    console.error("metrics/hit error", e);
    return null;
  }
}

// ---------------- РЕЗОЛВЕР ----------------
export async function resolveNews(slug) {
  const norm = normalizeSlug(slug);
  const paths = [
    `/news/resolve/${encodeURIComponent(norm)}/`,
    `/news/${encodeURIComponent(norm)}/`,
  ];
  const r = await tryGet(paths);
  return r.data;
}

// ---------------- СТРАНИЦЫ ----------------
export async function fetchPages() {
  const r = await api.get("/pages/");
  return r.data;
}

export async function fetchPage(slug) {
  const r = await api.get(`/pages/${slug}/`);
  return r.data;
}

// ---------------- ПРЕДЛОЖИТЬ НОВОСТЬ ----------------
export async function suggestNews(payload) {
  try {
    const r = await api.post("/news/suggest/", payload, {
      headers: { "Content-Type": "application/json" },
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

// ---------------- АДМИН ----------------
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
