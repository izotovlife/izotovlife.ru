// Путь: frontend/src/App.js
// Назначение: Корневой компонент SPA с SEO-маршрутами под Django backend.
// Обновления:
//   • Поддержка SEO-путей: /news/:category/:slug и /news/source/:source/:slug
//   • Поддержка короткого пути /news/:slug → resolve через API
//   • Совместимость со старыми путями /rss/:slug и /news/imported/...

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
import CategoryPage from "./pages/CategoryPage";
import NewsDetailPage from "./pages/NewsDetailPage";
import SearchPage from "./pages/SearchPage";
import AuthorPage from "./pages/AuthorPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import StaticPage from "./pages/StaticPage";

// Универсальный редирект для старых путей
function RedirectToCleanNews() {
  const location = useLocation();
  const parts = location.pathname.split("/");
  const slug = parts[parts.length - 1];
  return <Navigate to={`/news/${slug}`} replace />;
}

export default function App() {
  return (
    <Router>
      <div className="App">
        <Navbar />
        <HeaderInfo compact={true} />

        <Routes>
          {/* Главная лента */}
          <Route path="/" element={<FeedPage />} />

          {/* Категории */}
          <Route path="/categories" element={<CategoryPage />} />
          <Route path="/category/:slug" element={<CategoryPage />} />

          {/* Поиск и автор */}
          <Route path="/search" element={<SearchPage />} />
          <Route path="/author/:id" element={<AuthorPage />} />

          {/* ✅ SEO-маршруты новостей */}
          <Route path="/news/:category/:slug" element={<NewsDetailPage />} />
          <Route path="/news/source/:source/:slug" element={<NewsDetailPage />} />
          <Route path="/news/:slug" element={<NewsDetailPage />} />

          {/* ===== Легаси-редиректы ===== */}
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

          {/* Авторизация и статические страницы */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/pages/:slug" element={<StaticPage />} />

          {/* Фолбэк */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>

        <Footer />
      </div>
    </Router>
  );
}
