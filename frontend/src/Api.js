// frontend/src/Api.js
// Назначение: Axios-инстанс и функции API (логин, регистрация, восстановление пароля,
// работа с новостями, категории, авторские и редакторские статьи, админ URL).
// Обновления:
//   - Добавлена функция fetchNews(page) для главной ленты с пагинацией
//   - Старый fetchFeed больше не нужен (удалён, чтобы не путаться)
// Путь: frontend/src/Api.js

import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000/api", // ⚡ локальный бэкенд; в проде меняется через .env
});

// ===== JWT управление =====
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

// ===== АУТЕНТИФИКАЦИЯ =====
export async function login(username, password) {
  const r = await api.post("/auth/login/", { username, password });
  const token = r.data?.access;
  if (token) setToken(token);
  return r.data;
}

export async function whoami() {
  const token = localStorage.getItem("access");
  if (!token) return null;

  try {
    const r = await api.get("/auth/me/");
    return r.data;
  } catch (err) {
    if (err?.response?.status === 401) {
      return null;
    }
    throw err;
  }
}

// ===== АДМИН-ССЫЛКА =====
export async function adminSessionLogin() {
  const r = await api.post("/security/admin-session-login/");
  return r.data; // { admin_url: "..." }
}

export async function goToAdmin() {
  try {
    const r = await adminSessionLogin();
    let url = r.admin_url;

    if (url.startsWith("/")) {
      const base = api.defaults.baseURL.replace(/\/api$/, "");
      url = base + url;
    }

    console.log("Редирект в админку:", url);
    window.location.href = url;
  } catch (err) {
    console.error("Не удалось получить admin_url", err);
  }
}

// ===== ЛЕНТА =====
export async function fetchNews(page = 1) {
  const r = await api.get("/news/feed/", { params: { page } });
  return r.data; // {results, next, previous, count}
}

export async function fetchFeedText(page = 1) {
  const r = await api.get("/news/feed/text/", { params: { page } });
  return r.data;
}

export async function fetchFeedImages(page = 1) {
  const r = await api.get("/news/feed/images/", { params: { page } });
  return r.data;
}

// ===== КАТЕГОРИИ =====
export async function fetchCategories() {
  const r = await api.get("/news/categories/");
  return r.data;
}

export async function fetchCategoryNews(slug, page = 1) {
  const r = await api.get(`/news/category/${slug}/`, { params: { page } });
  return r.data;
}

// ===== ПОИСК =====
export async function searchAll(query, { limit = 30, offset = 0 } = {}) {
  const r = await api.get("/news/search/", {
    params: { q: query, limit, offset },
  });
  const data = r.data;

  return {
    items: data.results || data.items || (Array.isArray(data) ? data : []),
    total: data.count ?? data.total ?? (Array.isArray(data) ? data.length : 0),
  };
}

// ===== СТАТЬИ =====
export async function fetchArticle(slug) {
  const r = await api.get(`/news/article/${slug}/`);
  return r.data;
}

export async function fetchImportedNews(id) {
  const r = await api.get(`/news/rss/${id}/`);
  return r.data;
}

// ===== АВТОР =====
export async function fetchMyArticles() {
  const r = await api.get("/news/author/articles/");
  return r.data;
}

export async function fetchMyByStatus(status) {
  const r = await api.get("/news/author/articles/", { params: { status } });
  return r.data;
}

export async function createArticle(data) {
  const formData = new FormData();
  formData.append("title", data.title);
  formData.append("content", data.content);
  formData.append("status", data.status || "DRAFT");

  if (data.categories && data.categories.length > 0) {
    data.categories.forEach((catId) => formData.append("categories", catId));
  }

  if (data.cover_image) {
    formData.append("cover_image", data.cover_image);
  }

  const r = await api.post("/news/author/articles/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return r.data;
}

export async function updateArticle(id, data) {
  const formData = new FormData();
  formData.append("title", data.title);
  formData.append("content", data.content);
  formData.append("status", data.status || "DRAFT");

  if (data.categories && data.categories.length > 0) {
    data.categories.forEach((catId) => formData.append("categories", catId));
  }

  if (data.cover_image) {
    formData.append("cover_image", data.cover_image);
  }

  const r = await api.put(`/news/author/articles/${id}/`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return r.data;
}

export async function submitArticle(id) {
  const r = await api.post(`/news/author/articles/${id}/submit/`);
  return r.data;
}

export async function resubmitArticle(id) {
  const r = await api.post(`/news/author/articles/${id}/resubmit/`);
  return r.data;
}

export async function withdrawArticle(id) {
  const r = await api.post(`/news/author/articles/${id}/withdraw/`);
  return r.data;
}

// ===== РЕДАКТОР =====
export async function fetchModerationQueue() {
  const r = await api.get("/news/editor/moderation-queue/");
  return r.data;
}

export async function reviewArticle(id, action, editor_notes = "") {
  const r = await api.post(`/news/editor/review/${id}/${action}/`, {
    editor_notes,
  });
  return r.data;
}

// ===== СТАТИЧЕСКИЕ СТРАНИЦЫ =====
export async function fetchPages() {
  const r = await api.get("/pages/");
  return r.data;
}

export async function fetchPage(slug) {
  const r = await api.get(`/pages/${slug}/`);
  return r.data;
}

// ===== Регистрация и восстановление пароля =====
export async function register(data) {
  const r = await api.post("/auth/register/", data);
  return r.data;
}

export async function requestPasswordReset(data) {
  const r = await api.post("/auth/password-reset/", data);
  return r.data;
}

export async function confirmPasswordReset(uid, token, data) {
  const r = await api.post(
    `/auth/password-reset-confirm/${uid}/${token}/`,
    data
  );
  return r.data;
}

export default api;
