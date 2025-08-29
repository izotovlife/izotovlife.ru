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

export default api;
