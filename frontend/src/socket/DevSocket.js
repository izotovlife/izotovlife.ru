// Путь: frontend/src/socket/DevSocket.js
// Назначение: Безопасная инициализация dev-WebSocket только если задан WS_URL.
//   - Если WS_URL пустой — ничего не делаем (никаких ошибок в консоли).
//   - Если сервер недоступен — перестаём ретраить после пары попыток, чтобы не спамить.
//   - Никаких зависимостей от конкретных бандлеров/плагинов.

import { WS_URL } from "../config";

let socket = null;
let attempts = 0;
const MAX_ATTEMPTS = 2;

export function initDevSocket() {
  if (!WS_URL) {
    // Сокеты выключены конфигурацией — выходим молча
    return;
  }
  if (socket || attempts >= MAX_ATTEMPTS) return;

  try {
    attempts += 1;
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      // Успех — можно сбросить счётчик
      attempts = 0;
      // console.log("[WS] connected:", WS_URL);
    };

    socket.onmessage = (e) => {
      // Если захочешь что-то ловить — добавь здесь обработчики
      // console.log("[WS] message:", e.data);
    };

    socket.onclose = () => {
      socket = null;
      // Ещё одна попытка, но не больше MAX_ATTEMPTS
      if (attempts < MAX_ATTEMPTS) {
        setTimeout(initDevSocket, 1500);
      }
    };

    socket.onerror = () => {
      // Ошибку глушим, чтобы консоль не краснела
      try { socket && socket.close(); } catch {}
      socket = null;
    };
  } catch {
    socket = null;
  }
}
