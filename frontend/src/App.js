// Путь: frontend/src/App.js
// Назначение: Корневой компонент SPA IzotovLife с поддержкой коротких SEO-путей и кабинетами.
//
// Что внутри и важные заметки:
// - Порядок роутов: СНАЧАЛА специфические (активация, кабинеты, короткие служебные пути), ПОТОМ универсальные (/:slug, /:category/:slug).
// - Добавлены кабинеты: /dashboard/reader, /dashboard/author, /dashboard/editor (+ легаси-редиректы).
// - Добавлен короткий путь детальной авторской статьи: /a/:slug (расположен ВЫШЕ /:slug, чтобы не перехватывался категорией).
// - Старые пути категорий редиректят на короткие.
// - Прокси-страница активации аккаунта переносит на backend-страницу подтверждения.
// - ВАЖНО: BrowserRouter уже в frontend/src/index.js — здесь НЕТ обёртки <Router>.
//
// Изменения (редкий кейс удаления — ОБЯЗАТЕЛЕН для корректной работы):
//   ❌ Удалены старые привязки /author-dashboard → <ReaderPage/>.
//   ✅ Вместо них добавлены корректные маршруты кабинетов и редиректы на них.
//   ✅ Добавлен /a/:slug для ссылок из публичной страницы автора.

import React from "react";
import {
  Routes,
  Route,
  Navigate,
  useLocation,
  useParams,
} from "react-router-dom";

import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import HeaderInfo from "./components/HeaderInfo";

import FeedPage from "./pages/FeedPage";
import CategoryPage from "./pages/CategoryPage";     // страница одной категории (/:slug)
import CategoriesPage from "./pages/CategoryPage";   // список всех категорий (/categories) — легаси-совмещение
import NewsDetailPage from "./pages/NewsDetailPage";
import SearchPage from "./pages/SearchPage";
import AuthorPage from "./pages/AuthorPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import StaticPage from "./pages/StaticPage";
import SuggestPage from "./pages/SuggestPage";
// === Кабинет читателя (избранное) ===
import ReaderPage from "./pages/ReaderPage";
// === Кабинеты автора и редактора (добавлены) ===
import AuthorDashboard from "./pages/AuthorDashboard";
import EditorDashboard from "./pages/EditorDashboard";

// === Глобальная база backend API (для прокси-редиректов активации) ===
const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

// --- Редиректы для старых URL ---
function RedirectToCleanNews() {
  const params = useParams();
  const values = Object.values(params).filter(Boolean);
  const slug = values[values.length - 1];
  return <Navigate to={`/${slug}/`} replace />;
}

function RedirectOldCategory() {
  const { slug } = useParams();
  return <Navigate to={`/${slug}/`} replace />;
}

// --- Прокрутка к началу при смене маршрута ---
function ScrollToTopOnRouteChange() {
  const { pathname } = useLocation();
  React.useEffect(() => {
    try {
      window.scrollTo({ top: 0, behavior: "instant" });
    } catch {
      window.scrollTo(0, 0);
    }
  }, [pathname]);
  return null;
}

// --- Прокси-страница активации аккаунта ---
function ActivationProxy() {
  const { uid, token } = useParams();
  React.useEffect(() => {
    if (!uid || !token) return;
    const safeUid = encodeURIComponent(uid);
    const safeToken = encodeURIComponent(token);
    const url = `${API_BASE}/api/auth/activate/${safeUid}/${safeToken}/?html=1`;
    window.location.replace(url);
  }, [uid, token]);
  return (
    <div style={{ maxWidth: 520, margin: "40px auto", color: "#e6eefc" }}>
      <div
        style={{
          background: "#111a2b",
          padding: 24,
          borderRadius: 16,
          boxShadow: "0 10px 30px rgba(0,0,0,.35)",
        }}
      >
        <h1 style={{ marginTop: 0 }}>Подтверждение регистрации…</h1>
        <p>Перенаправляем вас на страницу активации аккаунта.</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <>
      <ScrollToTopOnRouteChange />
      <div className="App">
        <Navbar />
        <HeaderInfo compact={true} />

        <Routes>
          {/* 🏠 Главная */}
          <Route path="/" element={<FeedPage />} />

          {/* 🗂️ Старые пути категорий → редирект */}
          <Route path="/news/category/:slug" element={<RedirectOldCategory />} />
          <Route path="/category/:slug" element={<RedirectOldCategory />} />

          {/* ===================== КАБИНЕТЫ (ставим ВЫШЕ публичного /author/:id и коротких путей) ===================== */}
          {/* Современные пути кабинетов */}
          <Route path="/dashboard/reader" element={<ReaderPage />} />
          <Route path="/dashboard/reader/" element={<ReaderPage />} />

          <Route path="/dashboard/author" element={<AuthorDashboard />} />
          <Route path="/dashboard/author/" element={<AuthorDashboard />} />

          <Route path="/dashboard/editor" element={<EditorDashboard />} />
          <Route path="/dashboard/editor/" element={<EditorDashboard />} />

          {/* Базовый /dashboard → на кабинет читателя (чтобы было поведение «по умолчанию») */}
          <Route path="/dashboard" element={<Navigate to="/dashboard/reader/" replace />} />
          <Route path="/dashboard/" element={<Navigate to="/dashboard/reader/" replace />} />

          {/* Легаси-синонимы кабинетов */}
          <Route path="/cabinet" element={<Navigate to="/dashboard/reader/" replace />} />
          <Route path="/cabinet/" element={<Navigate to="/dashboard/reader/" replace />} />
          <Route path="/reader" element={<Navigate to="/dashboard/reader/" replace />} />
          <Route path="/reader/" element={<Navigate to="/dashboard/reader/" replace />} />
          <Route path="/author-dashboard" element={<Navigate to="/dashboard/author/" replace />} />
          <Route path="/author-dashboard/" element={<Navigate to="/dashboard/author/" replace />} />
          <Route path="/editor-dashboard" element={<Navigate to="/dashboard/editor/" replace />} />
          <Route path="/editor-dashboard/" element={<Navigate to="/dashboard/editor/" replace />} />
          {/* Легаси-ошибочные/служебные под /author/* → редиректы на кабинеты */}
          <Route path="/author/dashboard" element={<Navigate to="/dashboard/author/" replace />} />
          <Route path="/author/dashboard/" element={<Navigate to="/dashboard/author/" replace />} />
          <Route path="/author/editor" element={<Navigate to="/dashboard/editor/" replace />} />
          <Route path="/author/editor/" element={<Navigate to="/dashboard/editor/" replace />} />
          <Route path="/author/reader" element={<Navigate to="/dashboard/reader/" replace />} />
          <Route path="/author/reader/" element={<Navigate to="/dashboard/reader/" replace />} />

          {/* 🔍 Поиск, авторы и прочие страницы */}
          <Route path="/search" element={<SearchPage />} />

          {/* Публичная страница автора — ДОЛЖНА идти ПОСЛЕ кабинетов */}
          <Route path="/author/:id" element={<AuthorPage />} />

          {/* 🔐 Авторизация и статические */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/pages/:slug" element={<StaticPage />} />

          {/* 📨 Предложить новость */}
          <Route path="/suggest" element={<SuggestPage />} />

          {/* ✅ Активация аккаунта — выше универсальных путей */}
          <Route path="/activate/:uid/:token" element={<ActivationProxy />} />
          <Route path="/registration/confirm/:uid/:token" element={<ActivationProxy />} />

          {/* 📰 Детальные новости (для обратной совместимости) */}
          <Route path="/news/source/:source/:slug" element={<NewsDetailPage />} />
          <Route path="/news/:category/:slug" element={<NewsDetailPage />} />
          <Route path="/news/:slug" element={<NewsDetailPage />} />

          {/* ✅ Короткий путь детальной авторской статьи (используется в AuthorPage) */}
          <Route path="/a/:slug" element={<NewsDetailPage />} />
          <Route path="/a/:slug/" element={<NewsDetailPage />} />

          {/* ✅ Новые короткие пути */}
          {/* Список всех категорий */}
          <Route path="/categories" element={<CategoriesPage />} />
          <Route path="/categories/" element={<CategoriesPage />} /> {/* синоним со слэшем */}

          {/* Одна категория */}
          {/* ВАЖНО: /a/:slug уже объявлен выше, чтобы не перехватывался правилом ниже */}
          <Route path="/:slug" element={<CategoryPage />} />
          <Route path="/:slug/" element={<CategoryPage />} />

          {/* Детальные новости по коротким путям */}
          <Route path="/:category/:slug" element={<NewsDetailPage />} />
          <Route path="/:category/:slug/" element={<NewsDetailPage />} />

          {/* ===== Легаси редиректы ===== */}
          <Route path="/rss/:slug" element={<RedirectToCleanNews />} />
          <Route path="/news/a/:slugOrId" element={<RedirectToCleanNews />} />
          <Route path="/news/i/:slugOrId" element={<RedirectToCleanNews />} />
          <Route
            path="/news/imported/:sourceSlug/:importedSlug"
            element={<RedirectToCleanNews />}
          />
          <Route
            path="/news/:sourceSlug/:importedSlug"
            element={<RedirectToCleanNews />}
          />

          {/* 🚧 Фолбэк на главную */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        <Footer />
      </div>
    </>
  );
}
