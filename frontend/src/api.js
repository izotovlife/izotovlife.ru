// ===== ФАЙЛ: frontend/src/api.js =====
// ПУТЬ: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\frontend\src\api.js
// НАЗНАЧЕНИЕ: Конфигурация API для фронтенда (React ↔ Django backend)

import axios from "axios";

// Базовый URL всегда указывает на Django (порт 8000)
const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
  headers: {
    "Content-Type": "application/json",
  },
});

// Перехватчик для подстановки JWT токена (если есть)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access");
    if (token && token !== "null" && token !== "undefined") {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Автоматическое обновление access-токена при получении 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    const status = error.response ? error.response.status : null;

    if (status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh");

      if (refresh) {
        try {
          const { data } = await axios.post(
            "http://127.0.0.1:8000/api/token/refresh/",
            { refresh }
          );
          localStorage.setItem("access", data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch (refreshErr) {
          localStorage.removeItem("access");
          localStorage.removeItem("refresh");
          window.location.href = "/login";
          return Promise.reject(refreshErr);
        }
      }

      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

export default api;
