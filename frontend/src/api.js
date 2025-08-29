// ===== frontend/src/api.js =====
// Единый axios-клиент + очереди для безопасного refresh токена

import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/api/";

// Единый экземпляр клиента
const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// --- Хранилище токенов ---
function getAccess() {
  const t = localStorage.getItem("access");
  return t && t !== "null" && t !== "undefined" ? t : null;
}
function getRefresh() {
  const t = localStorage.getItem("refresh");
  return t && t !== "null" && t !== "undefined" ? t : null;
}
function setAccess(token) {
  localStorage.setItem("access", token);
}
function clearTokens() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
}

// --- Мьютекс для refresh, чтобы не было лавины запросов ---
let isRefreshing = false;
let refreshQueue = []; // массив промис-резолверов

function subscribeTokenRefresh(cb) {
  refreshQueue.push(cb);
}
function onRefreshed(newAccess) {
  refreshQueue.forEach((cb) => cb(newAccess));
  refreshQueue = [];
}

// --- Request: подставляем Bearer ---
api.interceptors.request.use(
  (config) => {
    const access = getAccess();
    if (access) {
      config.headers.Authorization = `Bearer ${access}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Функция рефреша (единственная «владеет» сетевым вызовом)
async function refreshAccessToken() {
  const refresh = getRefresh();
  if (!refresh) throw new Error("No refresh token");

  const { data } = await axios.post(`${API_BASE}token/refresh/`, { refresh });
  // Ожидаем, что backend возвращает { access, refresh? }
  if (data?.access) setAccess(data.access);
  return data?.access;
}

// --- Response: перехват 401 с очередью ---
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const status = error?.response?.status;
    const original = error?.config;

    // Если не 401 — отдать как есть
    if (status !== 401 || original?._retry) {
      return Promise.reject(error);
    }

    // Помечаем, что этот запрос уже будет повторён один раз
    original._retry = true;

    // Если уже идёт refresh — подпишемся и дождёмся
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        subscribeTokenRefresh((newAccess) => {
          if (newAccess) {
            original.headers.Authorization = `Bearer ${newAccess}`;
            resolve(api(original));
          } else {
            reject(error);
          }
        });
      });
    }

    // Мы первые: запускаем refresh
    isRefreshing = true;
    try {
      const newAccess = await refreshAccessToken();
      isRefreshing = false;
      onRefreshed(newAccess);
      // повторим оригинальный запрос
      if (newAccess) {
        original.headers.Authorization = `Bearer ${newAccess}`;
      }
      return api(original);
    } catch (refreshErr) {
      isRefreshing = false;
      onRefreshed(null); // разбудим ожидающих с неуспехом
      clearTokens();
      // один редирект на всех
      if (window.location.pathname !== "/login") {
        window.location.replace("/login");
      }
      return Promise.reject(refreshErr);
    }
  }
);

export default api;

// (опционально) удобные обёртки для сервисов:
export const AccountsAPI = {
  getProfile: () => api.get("accounts/profile/"),
  updateProfile: (payload) => api.patch("accounts/profile/", payload), // PATCH для частичных обновлений
};

export const AuthAPI = {
  login: async (username, password) => {
    const { data } = await axios.post(`${API_BASE}token/`, { username, password });
    if (data?.access) localStorage.setItem("access", data.access);
    if (data?.refresh) localStorage.setItem("refresh", data.refresh);
    return data;
  },
  logout: () => {
    clearTokens();
    window.location.replace("/login");
  },
};

export const NewsAPI = {
  list: (page = 1) => api.get(`news/?page=${page}`),
  popular: () => api.get("news/popular/"),
  detail: (id) => api.get(`news/${id}/`),
};
