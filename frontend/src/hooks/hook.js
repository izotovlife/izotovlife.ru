// Путь: frontend/src/hooks/hook.js
// Назначение: централизованные запросы (включая вход в закрытую админку по одноразовому токену),
// обработка ошибок сети (в т.ч. wttr.in), хелперы для новостей.

import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:8000";

// === Безопасный GET: не валим приложение, если ответ не 2xx ===
export async function tryGet(url, config = {}) {
  try {
    const resp = await axios.get(url, { withCredentials: false, ...config });
    return { ok: true, data: resp.data, status: resp.status };
  } catch (err) {
    console.error("tryGet error:", err);
    return { ok: false, error: err, status: err?.response?.status || 0 };
  }
}

// === Безопасный POST JSON: гарантируем Content-Type и JSON.stringify ===
export async function postJson(url, body, config = {}) {
  try {
    const resp = await axios.post(url, body, {
      withCredentials: false,
      headers: { "Content-Type": "application/json" },
      transformRequest: [
        (data, headers) => {
          // Если нам подсунули строку — не трогаем; если объект — сериализуем
          if (typeof data === "string") return data;
          try {
            return JSON.stringify(data ?? {});
          } catch {
            // На крайний случай отдадим пустой JSON
            return "{}";
          }
        },
      ],
      ...config,
    });
    return { ok: true, data: resp.data, status: resp.status };
  } catch (err) {
    console.error("postJson error:", err);
    return { ok: false, error: err, status: err?.response?.status || 0, data: err?.response?.data };
  }
}

// === Вход в закрытую админку через одноразовый токен ===
export async function adminSessionLogin(username, password) {
  const url = `${API_BASE}/api/security/admin-session-login/`; // бэкенд ждёт именно так
  const res = await postJson(url, { username, password });

  if (!res.ok) {
    // Покажем ровно то, что вернул сервер (например, "Invalid JSON" / "username/password required")
    const serverText = typeof res.data === "string" ? res.data : JSON.stringify(res.data);
    throw new Error(`Admin login failed (${res.status}): ${serverText}`);
  }

  if (!res.data?.redirect || typeof res.data.redirect !== "string") {
    throw new Error("Admin login: отсутствует redirect в ответе API");
  }
  return res.data.redirect; // вида: /admin/<token>/
}

// === Погода: wttr.in иногда отдает не JSON (503). Отлавливаем. ===
export async function fetchWeather(lat, lon) {
  const weatherUrl = `https://wttr.in/${lat},${lon}?format=j1&lang=ru`;
  try {
    const r = await axios.get(weatherUrl, { timeout: 6000 });
    if (typeof r.data === "object") return { ok: true, data: r.data };
    // Если пришла строка — это не JSON
    return { ok: false, error: new Error("wttr returned non-JSON") };
  } catch (e) {
    console.warn("Погода недоступна, пропускаю:", e?.message || e);
    return { ok: false, error: e };
  }
}

// === Хелпер: построение API URL для детальной новости ===
// Мы придерживаемся схемы: /api/news/rss/source/<source>/<slug>/
// Если бэк поддерживает короткий путь /api/news/rss/<slug>/ — можно переключить strategy.
export function buildNewsApiDetailUrl({ source, slug }, strategy = "withSource") {
  if (strategy === "withSource") {
    return `${API_BASE}/api/news/rss/source/${encodeURIComponent(source)}/${encodeURIComponent(slug)}/`;
  }
  // запасной вариант (если на бэке включили короткий роут)
  return `${API_BASE}/api/news/rss/${encodeURIComponent(slug)}/`;
}

// Related: аналогично
export function buildNewsApiRelatedUrl({ source, slug }, strategy = "withSource") {
  if (strategy === "withSource") {
    return `${API_BASE}/api/news/rss/source/${encodeURIComponent(source)}/${encodeURIComponent(slug)}/related/`;
  }
  return `${API_BASE}/api/news/rss/${encodeURIComponent(slug)}/related/`;
}
