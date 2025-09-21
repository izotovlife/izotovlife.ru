// frontend/src/components/Navbar.js
// Назначение: фиксированная шапка (логотип, поиск, меню)
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
    <header className="navbar">
      <div className="navbar-container">
        {/* Логотип слева */}
        <Link to="/" className="navbar-logo">
          IzotovLife
        </Link>

        {/* Поиск и бургер справа */}
        <div className="right-controls">
          {showSearch ? (
            <div className="search-box">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Поиск..."
              />
              <button onClick={handleSearch}>
                <FaArrowRight />
              </button>
            </div>
          ) : (
            <button
              className="search-btn"
              onClick={() => setShowSearch(true)}
            >
              <FaSearch />
            </button>
          )}

          <div className="burger-wrapper">
            <button
              className="burger"
              onClick={() => setOpen(!open)}
              aria-label="Меню"
            >
              ☰
            </button>
            {open && (
              <div className="dropdown-menu">
                <Link to="/search" onClick={() => setOpen(false)}>
                  Поиск
                </Link>
                <Link to="/categories" onClick={() => setOpen(false)}>
                  Категории
                </Link>

                {!user && (
                  <>
                    <Link to="/login" onClick={() => setOpen(false)}>
                      Войти
                    </Link>
                    <Link to="/register" onClick={() => setOpen(false)}>
                      Регистрация
                    </Link>
                  </>
                )}

                {user && (
                  <>
                    {/* ✅ Аккаунт теперь ведёт в Django-редирект */}
                    <a
                      href="/accounts/account-redirect/"
                      onClick={() => setOpen(false)}
                    >
                      Аккаунт
                    </a>

                    {/* Выйти */}
                    <button onClick={handleLogout} className="logout-btn">
                      Выйти
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        .navbar {
          background: #fff;
          color: #222;
          border-bottom: 1px solid #ddd;
          position: sticky;
          top: 0;
          z-index: 50;
        }
        .navbar-container {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 10px 16px;
        }
        .navbar-logo {
          font-weight: bold;
          text-decoration: none;
          color: #222;
        }
        .right-controls {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .search-btn {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #333;
        }
        .search-box {
          display: flex;
          align-items: center;
          border: 1px solid #ddd;
          border-radius: 20px;
          padding: 2px 6px;
          background: #f9f9f9;
        }
        .search-box input {
          border: none;
          outline: none;
          background: transparent;
          padding: 4px 8px;
          width: 150px;
        }
        .search-box button {
          background: none;
          border: none;
          cursor: pointer;
          font-size: 16px;
          color: #0077ff;
        }
        .burger-wrapper {
          position: relative;
        }
        .burger {
          font-size: 22px;
          background: none;
          border: none;
          color: #222;
          cursor: pointer;
        }
        .dropdown-menu {
          position: absolute;
          top: 40px;
          right: 0;
          background: #fff;
          border: 1px solid #ddd;
          border-radius: 6px;
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
          display: flex;
          flex-direction: column;
          min-width: 160px;
          z-index: 1000;
        }
        .dropdown-menu a, .dropdown-menu button {
          padding: 10px;
          text-align: left;
          color: #222;
          text-decoration: none;
          background: none;
          border: none;
          cursor: pointer;
        }
        .dropdown-menu a:hover, .dropdown-menu button:hover {
          background: #f2f2f2;
        }
      `}</style>
    </header>
  );
}

export default Navbar;
