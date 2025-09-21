// frontend/src/Api.js
// Назначение: Axios-инстанс и функции API (устойчивый логин, работа с новостями, категории, авторские статьи, модерация редактора, статические страницы).
// Путь: frontend/src/Api.js

import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
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

// ——— ВСПОМОГАТЕЛЬНОЕ: достать токен
function extractAccessToken(data) {
  if (!data) return null;
  return (
    data.access ||
    data.access_token ||
    data.token ||
    (data.tokens && (data.tokens.access || data.tokens.access_token)) ||
    null
  );
}

/** ===== Новая функция для уникального admin URL ===== */
export async function adminSessionLogin() {
  // Бэкенд ждёт только авторизацию по JWT → передавать username/password не нужно
  const { data } = await api.post("/api/security/admin-session-login/");
  return data;
}

/** ===== УСТОЙЧИВЫЙ ЛОГИН ===== */
export async function login(loginField, password) {
  delete api.defaults.headers.common["Authorization"];

  async function doLogin(body) {
    const { data } = await api.post("/api/auth/login/", body, {
      headers: { Authorization: undefined },
    });
    const tok = extractAccessToken(data);
    if (!tok) throw new Error("Не найден токен в ответе сервера");
    setToken(tok);
    return data;
  }

  try {
    return await doLogin({ username: loginField, password });
  } catch (err1) {
    if (err1?.response?.status && err1.response.status !== 400) {
      throw err1;
    }
    try {
      return await doLogin({ email: loginField, password });
    } catch (err2) {
      const resp = err2?.response || err1?.response;
      const msg =
        resp?.data?.detail ||
        resp?.data?.non_field_errors?.[0] ||
        JSON.stringify(resp?.data) ||
        "Ошибка входа";
      const e = new Error(msg);
      e.response = resp;
      throw e;
    }
  }
}

// Текущий пользователь
export async function whoami() {
  const { data } = await api.get("/api/auth/me/");
  return data;
}

/** ===== Публичные API ===== */
export async function fetchFeed(params = {}) {
  const { data } = await api.get("/api/news/feed/", {
    params,
    headers: { Authorization: undefined },
  });
  return data;
}

export async function searchAll(q, params = {}) {
  const { data } = await api.get("/api/news/search/", {
    params: { q, ...params },
    headers: { Authorization: undefined },
  });
  return {
    items: data.results || [],
    total: data.count || 0,
    next: data.next,
    previous: data.previous,
  };
}

export async function fetchCategories() {
  const { data } = await api.get("/api/news/categories/", {
    headers: { Authorization: undefined },
  });
  return data;
}

export async function fetchArticle(slug) {
  const { data } = await api.get(`/api/news/article/${slug}/`, {
    headers: { Authorization: undefined },
  });
  return data;
}

export async function fetchImportedNews(id) {
  const { data } = await api.get(`/api/news/rss/${id}/`, {
    headers: { Authorization: undefined },
  });
  return data;
}

export async function fetchCategoryNews(slug, params = {}) {
  const { data } = await api.get(`/api/news/category/${slug}/`, {
    params,
    headers: { Authorization: undefined },
  });
  return data;
}

/** ===== Приватные (автор) ===== */
export async function fetchMyArticles() {
  const { data } = await api.get("/api/news/author/articles/");
  return data;
}

// ✅ Вернули для совместимости с AuthorDashboard
export async function fetchMyByStatus(status) {
  const { data } = await api.get("/api/news/author/articles/", {
    params: { status },
  });
  return data;
}

export async function createArticle(article) {
  const { data } = await api.post("/api/news/author/articles/", article);
  return data;
}

export async function updateArticle(id, article) {
  const { data } = await api.put(`/api/news/author/articles/${id}/`, article);
  return data;
}

export async function submitArticle(id) {
  const { data } = await api.post(`/api/news/author/articles/${id}/submit/`);
  return data;
}

/** ===== Редактор ===== */
export async function fetchModerationQueue() {
  const { data } = await api.get("/api/news/author/moderation-queue/");
  return data;
}

export async function reviewArticle(id, action, notes) {
  const { data } = await api.post(`/api/news/author/review/${id}/${action}/`, {
    notes,
  });
  return data;
}

/** ===== Статические страницы (футер) ===== */
export async function fetchPages() {
  const { data } = await api.get("/api/pages/", {
    headers: { Authorization: undefined },
  });

  if (Array.isArray(data)) {
    return data;
  }
  if (data && data.results) {
    return data.results;
  }
  return [];
}

export async function fetchPage(slug) {
  const { data } = await api.get(`/api/pages/${slug}/`, {
    headers: { Authorization: undefined },
  });
  return data;
}

export default api;
