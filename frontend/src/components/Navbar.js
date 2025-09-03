// frontend/src/components/Navbar.js
// Шапка сайта: логотип слева, категории по центру (жирным + hover),
// справа — поиск и иконка "гамбургер" с выпадающим меню (Вход/Регистрация).
// Меню позиционируется ПОД иконкой, не перекрывает поиск, высокий z-index,
// закрытие по клику вне и по Esc. Зависимости: react, react-router-dom.

import React, { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

// Поменяй путь к логотипу при необходимости
import logo from "../assets/logo.png";

function Navbar() {
  const navigate = useNavigate();

  const [menuOpen, setMenuOpen] = useState(false);
  const [q, setQ] = useState("");

  const menuRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    function onDocClick(e) {
      if (!menuOpen) return;
      const menuEl = menuRef.current;
      const btnEl = buttonRef.current;
      if (!menuEl || !btnEl) return;
      const clickedInsideMenu = menuEl.contains(e.target);
      const clickedButton = btnEl.contains(e.target);
      if (!clickedInsideMenu && !clickedButton) setMenuOpen(false);
    }
    function onEsc(e) {
      if (e.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onEsc);
    };
  }, [menuOpen]);

  const categories = [
    { to: "/news", label: "Новости" },
    { to: "/popular", label: "Популярное" },
    { to: "/world", label: "Мир" },
    { to: "/tech", label: "Технологии" },
    { to: "/business", label: "Бизнес" },
  ];

  const onSearchSubmit = (e) => {
    e.preventDefault();
    const query = q.trim();
    if (!query) return;
    navigate(`/search?q=${encodeURIComponent(query)}`);
    setMenuOpen(false);
  };

  return (
    <header className="bg-white shadow sticky top-0 z-40">
      <div className="container mx-auto">
        {/* Верхняя строка шапки */}
        <div className="flex items-center justify-between gap-4 px-3 py-2">
          {/* ЛОГО слева */}
          <Link to="/" className="shrink-0 flex items-center">
            <img
              src={logo}
              alt="IzotovLife"
              className="h-10 w-auto object-contain"
            />
          </Link>

          {/* Категории по центру (десктоп) */}
          <div
            role="navigation"
            className="hidden lg:flex flex-1 items-center justify-center"
          >
            <ul className="flex gap-6">
              {categories.map((c) => (
                <li key={c.to}>
                  <NavLink
                    to={c.to}
                    className={({ isActive }) =>
                      [
                        "font-semibold transition-colors",
                        isActive
                          ? "text-blue-600"
                          : "text-gray-800 hover:text-blue-600",
                      ].join(" ")
                    }
                  >
                    {c.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>

          {/* Поиск + бургер справа */}
          <div className="flex items-center gap-3">
            {/* Поиск (десктоп) */}
            <form onSubmit={onSearchSubmit} className="hidden md:flex">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                type="search"
                placeholder="Поиск по сайту…"
                className="border border-gray-300 rounded-lg px-3 py-2 w-56 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Поиск"
              />
            </form>

            {/* Контейнер бургера для относительного позиционирования меню */}
            <div className="relative">
              <button
                ref={buttonRef}
                type="button"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                aria-label="Открыть меню"
                onClick={() => setMenuOpen((v) => !v)}
                className="inline-flex items-center justify-center h-10 w-10 rounded-lg border border-gray-300 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {/* SVG-иконка бургер */}
                <svg
                  width="22"
                  height="22"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M3 6h18M3 12h18M3 18h18"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>

              {/* Выпадающее меню — ПОД иконкой */}
              {menuOpen && (
                <div
                  ref={menuRef}
                  role="menu"
                  className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-gray-200 bg-white shadow-xl z-50"
                >
                  <ul className="py-1">
                    <li>
                      <Link
                        to="/login"
                        role="menuitem"
                        className="block px-4 py-2 text-gray-800 hover:bg-gray-50"
                        onClick={() => setMenuOpen(false)}
                      >
                        Войти
                      </Link>
                    </li>
                    <li>
                      <Link
                        to="/register"
                        role="menuitem"
                        className="block px-4 py-2 text-gray-800 hover:bg-gray-50"
                        onClick={() => setMenuOpen(false)}
                      >
                        Регистрация
                      </Link>
                    </li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Категории + поиск для мобильных */}
        <div className="lg:hidden border-t border-gray-100">
          <div role="navigation" className="px-3 py-2">
            <ul className="flex gap-4 overflow-x-auto no-scrollbar">
              {categories.map((c) => (
                <li key={c.to}>
                  <NavLink
                    to={c.to}
                    className={({ isActive }) =>
                      [
                        "whitespace-nowrap font-semibold transition-colors",
                        isActive
                          ? "text-blue-600"
                          : "text-gray-800 hover:text-blue-600",
                      ].join(" ")
                    }
                  >
                    {c.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>

          <div className="px-3 pb-3">
            <form onSubmit={onSearchSubmit}>
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                type="search"
                placeholder="Поиск по сайту…"
                className="border border-gray-300 rounded-lg px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Поиск"
              />
            </form>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
