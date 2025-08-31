// frontend/src/components/Navbar.js
// Верхнее меню сайта: логотип слева, категории по центру, вход/регистрация справа

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Navbar() {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetch("/api/news/categories/")
      .then(res => res.json())
      .then(data => setCategories(data))
      .catch(() => setCategories([]));
  }, []);

  return (
    <nav>
      {/* Логотип */}
      <Link to="/" className="font-bold text-xl hover:underline">
        IzotovLife
      </Link>

      {/* Категории */}
      <div className="nav-links">
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
      <div className="auth-links">
        <Link to="/register" className="hover:underline">Регистрация</Link>
        <Link to="/login" className="hover:underline">Вход</Link>
      </div>
    </nav>
  );
}

export default Navbar;
