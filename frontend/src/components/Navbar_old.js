// frontend/src/components/Navbar.js
// Назначение: фиксированная шапка (логотип слева, поиск и меню справа)
// Путь: frontend/src/components/Navbar.js

import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { whoami, setToken } from "../Api";
import { FaSearch, FaArrowRight } from "react-icons/fa";

function Navbar() {
  const [open, setOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [showSearch, setShowSearch] = useState(false);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    async function loadUser() {
      try {
        const data = await whoami();
        setUser(data);
      } catch {
        setUser(null);
      }
    }
    loadUser();
  }, []);

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    navigate("/");
  };

  const handleSearch = () => {
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query)}`);
      setShowSearch(false);
      setQuery("");
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Логотип слева */}
        <Link to="/" className="text-xl font-bold text-gray-900">
          IzotovLife
        </Link>

        {/* Контролы справа */}
        <div className="flex items-center gap-4">
          {showSearch ? (
            <div className="flex items-center border border-gray-300 rounded-full px-2 bg-gray-50">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Поиск..."
                className="bg-transparent outline-none px-2 py-1 w-40"
              />
              <button onClick={handleSearch} className="text-blue-600">
                <FaArrowRight />
              </button>
            </div>
          ) : (
            <button
              className="text-gray-700 hover:text-black"
              onClick={() => setShowSearch(true)}
            >
              <FaSearch />
            </button>
          )}

          <div className="relative">
            <button
              className="text-gray-800 text-2xl"
              onClick={() => setOpen(!open)}
              aria-label="Меню"
            >
              ☰
            </button>
            {open && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg flex flex-col z-50">
                <Link
                  to="/search"
                  onClick={() => setOpen(false)}
                  className="px-4 py-2 hover:bg-gray-100"
                >
                  Поиск
                </Link>
                <Link
                  to="/categories"
                  onClick={() => setOpen(false)}
                  className="px-4 py-2 hover:bg-gray-100"
                >
                  Категории
                </Link>

                {!user && (
                  <>
                    <Link
                      to="/login"
                      onClick={() => setOpen(false)}
                      className="px-4 py-2 hover:bg-gray-100"
                    >
                      Войти
                    </Link>
                    <Link
                      to="/register"
                      onClick={() => setOpen(false)}
                      className="px-4 py-2 hover:bg-gray-100"
                    >
                      Регистрация
                    </Link>
                  </>
                )}

                {user && (
                  <>
                    <a
                      href="/accounts/account-redirect/"
                      onClick={() => setOpen(false)}
                      className="px-4 py-2 hover:bg-gray-100"
                    >
                      Аккаунт
                    </a>
                    <button
                      onClick={handleLogout}
                      className="px-4 py-2 text-left hover:bg-gray-100"
                    >
                      Выйти
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
