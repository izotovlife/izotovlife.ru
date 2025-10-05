// Путь: frontend/src/config.js
// Назначение: Единая конфигурация фронтенда (API, список новостей, статика, опциональный WebSocket).
// Считывает переменные из .env и нормализует URL, чтобы убрать "двойные слэши".
// Ничего критичного не меняет в логике — это тонкий слой над окружением.

function trimRightSlash(s) {
  return String(s || "").replace(/\/+$/, "");
}
function trimLeftSlash(s) {
  return String(s || "").replace(/^\/+/, "");
}
export function joinUrl(base, path = "") {
  const b = trimRightSlash(base);
  const p = trimLeftSlash(path);
  return p ? `${b}/${p}` : b;
}

// --- Значения из окружения ---
export const API_BASE =
  trimRightSlash(process.env.REACT_APP_API_BASE || "http://localhost:8000/api");

// Можно указывать с ведущим слэшем или без — мы нормализуем
const RAW_API_LIST_PATH = process.env.REACT_APP_API_LIST_PATH || "/news/";
export const API_LIST_PATH = `/${trimLeftSlash(RAW_API_LIST_PATH)}`; // хранить в виде "/news/"

export const STATIC_FALLBACK =
  process.env.REACT_APP_STATIC_FALLBACK || "/static/img/default_news.svg";

// Пустая строка = сокеты выключены (и консоль чистая)
export const WS_URL = (process.env.REACT_APP_WS_URL || "").trim();

// --- Удобные производные ---
export const NEWS_LIST_URL = joinUrl(API_BASE, API_LIST_PATH); // готовый абсолютный URL списка
export const apiPath = (subpath) => joinUrl(API_BASE, subpath); // сборщик путей к API

