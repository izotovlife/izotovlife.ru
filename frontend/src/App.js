// frontend/src/App.js
// Назначение: Корневой компонент SPA с маршрутизацией.
// Добавлено:
//   • Легаси-маршрут /rss/:id → редирект на /news/imported/:id (устраняет предупреждение "No routes matched").
// Остальные маршруты и структура — без изменений.
// Путь: frontend/src/App.js

import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Общие компоненты
import Navbar from "./components/Navbar";
import CategoriesBar from "./components/CategoriesBar";
import Footer from "./components/Footer";

// Страницы
import FeedPage from "./pages/FeedPage";
import CategoryPage from "./pages/CategoryPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";            // ✅ регистрация
import ResetPasswordPage from "./pages/ResetPasswordPage";  // ✅ запрос сброса пароля
import NewPasswordPage from "./pages/NewPasswordPage";      // ✅ ввод нового пароля
import AuthorDashboard from "./pages/AuthorDashboard";
import EditorDashboard from "./pages/EditorDashboard";
import SearchPage from "./pages/SearchPage";
import NewsDetailPage from "./pages/NewsDetailPage";
import AllCategoriesPage from "./pages/AllCategoriesPage";
import StaticPage from "./pages/StaticPage";                // ✅ статические страницы
import RssRedirect from "./pages/RssRedirect";              // ✅ легаси-редирект

export default function App() {
  return (
    <Router>
      <Navbar />
      <CategoriesBar />

      <div className="container mx-auto px-4 py-6">
        <Routes>
          {/* Главная лента */}
          <Route path="/" element={<FeedPage />} />

          {/* Категории */}
          <Route path="/category/:slug" element={<CategoryPage />} />
          <Route path="/categories" element={<AllCategoriesPage />} />

          {/* Детальная новость (Article или Imported) */}
          <Route path="/news/:type/:slugOrId" element={<NewsDetailPage />} />
          <Route path="/news/:slugOrId" element={<NewsDetailPage />} />

          {/* ✅ Легаси: старые ссылки вида /rss/123 → /news/imported/123 */}
          <Route path="/rss/:id" element={<RssRedirect />} />

          {/* Авторизация */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Восстановление пароля */}
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/reset-password/:uid/:token" element={<NewPasswordPage />} />

          {/* Кабинеты */}
          <Route path="/author" element={<AuthorDashboard />} />
          <Route path="/editor" element={<EditorDashboard />} />

          {/* Поиск */}
          <Route path="/search" element={<SearchPage />} />

          {/* Статические страницы */}
          <Route path="/page/:slug" element={<StaticPage />} />
        </Routes>
      </div>

      <Footer />
    </Router>
  );
}
