// Путь: frontend/src/App.js
// Назначение: Корневой компонент SPA IzotovLife с поддержкой коротких SEO-путей.
// Исправлено:
//   ✅ Категории теперь открываются по /<slug>/ (например /politika/).
//   ✅ /categories отображает сетку всех категорий.
//   ✅ Старые пути /news/category/... и /category/... редиректят на новый формат.
//   ✅ Удалён несуществующий импорт CategoriesPage.js.
//   ✅ Правильный порядок маршрутов (специфические → общие).
//   ✅ Полная совместимость с Django backend.

import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";

import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import HeaderInfo from "./components/HeaderInfo";

import FeedPage from "./pages/FeedPage";
import CategoryPage from "./pages/CategoryPage"; // ✅ единый компонент категорий
import NewsDetailPage from "./pages/NewsDetailPage";
import SearchPage from "./pages/SearchPage";
import AuthorPage from "./pages/AuthorPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import StaticPage from "./pages/StaticPage";
import SuggestPage from "./pages/SuggestPage";

// --- Редиректы для старых URL ---
function RedirectToCleanNews() {
  const location = useLocation();
  const parts = location.pathname.split("/").filter(Boolean);
  const slug = parts[parts.length - 1];
  return <Navigate to={`/${slug}/`} replace />;
}

function RedirectOldCategory() {
  const slug = window.location.pathname.split("/").pop();
  return <Navigate to={`/${slug}/`} replace />;
}

export default function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <HeaderInfo compact={true} />

        <Routes>
          {/* 🏠 Главная страница */}
          <Route path="/" element={<FeedPage />} />

          {/* 🗂️ Старые пути категорий → редирект */}
          <Route path="/news/category/:slug" element={<RedirectOldCategory />} />
          <Route path="/category/:slug" element={<RedirectOldCategory />} />

          {/* 🔍 Поиск, авторы и прочие страницы */}
          <Route path="/search" element={<SearchPage />} />
          <Route path="/author/:id" element={<AuthorPage />} />

          {/* 📰 Детальные новости (для обратной совместимости) */}
          <Route path="/news/source/:source/:slug" element={<NewsDetailPage />} />
          <Route path="/news/:category/:slug" element={<NewsDetailPage />} />
          <Route path="/news/:slug" element={<NewsDetailPage />} />

          {/* ✅ Новые короткие пути */}
          {/* Категории верхнего уровня */}
          <Route path="/categories" element={<CategoryPage />} />
          <Route path="/:slug/" element={<CategoryPage />} />

          {/* Детальные новости по коротким путям (например /politika/rossiya-startuet/) */}
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

          {/* 🔐 Авторизация и статические страницы */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/pages/:slug" element={<StaticPage />} />

          {/* 📨 Предложить новость */}
          <Route path="/suggest" element={<SuggestPage />} />

          {/* 🚧 Фолбэк на главную */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        <Footer />
      </div>
    </Router>
  );
}
