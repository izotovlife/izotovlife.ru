// frontend/src/App.js
// Назначение: Корневой компонент SPA с маршрутизацией.
// Путь: frontend/src/App.js

import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Общие компоненты
import Navbar from "./components/Navbar";
import CategoriesBar from "./components/CategoriesBar";
import Footer from "./components/Footer"; // ✅ добавили футер

// Страницы
import FeedPage from "./pages/FeedPage";
import CategoryPage from "./pages/CategoryPage";
import LoginPage from "./pages/LoginPage";
import AuthorDashboard from "./pages/AuthorDashboard";
import EditorDashboard from "./pages/EditorDashboard";
import SearchPage from "./pages/SearchPage";
import NewsDetailPage from "./pages/NewsDetailPage";
import AllCategoriesPage from "./pages/AllCategoriesPage";
import StaticPage from "./pages/StaticPage"; // ✅ статические страницы

// Восстановление пароля
import PasswordResetPage from "./pages/PasswordResetPage";
import PasswordResetConfirmPage from "./pages/PasswordResetConfirmPage";

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

          {/* Новость (Article или RSS) */}
          <Route path="/:type/:slugOrId" element={<NewsDetailPage />} />

          {/* Авторизация */}
          <Route path="/login" element={<LoginPage />} />

          {/* Восстановление пароля */}
          <Route path="/password-reset" element={<PasswordResetPage />} />
          <Route
            path="/password-reset-confirm/:uid/:token"
            element={<PasswordResetConfirmPage />}
          />

          {/* Кабинеты */}
          <Route path="/author" element={<AuthorDashboard />} />
          <Route path="/editor" element={<EditorDashboard />} />

          {/* Поиск */}
          <Route path="/search" element={<SearchPage />} />

          {/* Статические страницы (Политика, О компании и т.п.) */}
          <Route path="/page/:slug" element={<StaticPage />} />
        </Routes>
      </div>

      {/* ✅ Футер подключаем здесь */}
      <Footer />
    </Router>
  );
}
