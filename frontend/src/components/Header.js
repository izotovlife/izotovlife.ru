// frontend/src/components/Header.js
// Шапка сайта с логотипом и выбором категорий
// frontend/src/components/Navbar.js
// Верхнее меню сайта: логотип слева (только картинка), категории по центру, вход/регистрация справа

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import logo from "../assets/logo.png"; // твой логотип, положи в src/assets/logo.png

function Navbar() {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetch("/api/news/categories/")
      .then(res => res.json())
      .then(data => setCategories(data))
      .catch(() => setCategories([]));
  }, []);

  return (
    <nav className="flex items-center justify-between px-6 bg-[var(--color-header)] h-14">
      {/* Логотип (только картинка) */}
      <Link to="/" className="flex items-center hover:opacity-80">
        <img
          src={logo}
          alt="Logo"
          className="h-9 w-auto relative top-1"
        />
        {/* ↑ h-9 делает логотип немного больше, top-1 чуть опускает вниз */}
      </Link>

      {/* Категории */}
      <div className="nav-links flex gap-5 text-white">
        {categories.map(cat => (
          <Link
            key={cat.id}
            to={`/category/${cat.slug}`}
            className="hover:underline"
          >
            {cat.name}
          </Link>
        ))}
      </div>

      {/* Вход / Регистрация */}
      <div className="auth-links flex gap-4 text-white">
        <Link to="/register" className="hover:underline">Регистрация</Link>
        <Link to="/login" className="hover:underline">Вход</Link>
      </div>
    </nav>
  );
}

export default Navbar;
