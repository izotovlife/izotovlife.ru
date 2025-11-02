// Путь: frontend/src/index.js
// Назначение: Точка входа фронтенда, подключение App, HelmetProvider и BrowserRouter с future-флагами v7.
// Что внутри:
// - React 18 createRoot()
// - BrowserRouter с future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
// - HelmetProvider для SEO-мета-тегов
// - Подключение глобальных стилей
//
// ВАЖНО: Если <BrowserRouter> уже есть внутри App.js — удалите его там, чтобы не было двойного роутера.
import "./Api";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";      // ← добавлено
import App from "./App";
import "./index.css";

// SEO: HelmetProvider
import { HelmetProvider } from "react-helmet-async";

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <HelmetProvider>
        <App />
      </HelmetProvider>
    </BrowserRouter>
  </React.StrictMode>
);



