// Путь: frontend/src/index.js
// Назначение: Точка входа React-приложения.
// Обновление: добавлен безопасный вызов initDevSocket() — он молчит, если WS выключен.

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

// ✅ добавляем:
import { initDevSocket } from "./socket/DevSocket";
initDevSocket();

// --- ниже оставь весь твой текущий код, я просто показываю каноническую схему ---
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);



