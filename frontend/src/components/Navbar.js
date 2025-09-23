// frontend/src/components/Navbar.js
// Назначение: фиксированная шапка (логотип, гамбургер меню, поиск, переключатель версий слабовидящих через иконку + горячие клавиши Alt+0..2)
// Путь: frontend/src/components/Navbar.js

import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { whoami, setToken } from "../Api";
import { FaSearch, FaBars, FaTimes } from "react-icons/fa";
import { ReactComponent as Logo } from "../assets/izotovlife_logo.svg";

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [query, setQuery] = useState("");
  const [user, setUser] = useState(null);

  // ✅ убрали black-режим
  const themes = ["normal", "low-vision-yellow", "low-vision-white"];
  const [theme, setTheme] = useState(localStorage.getItem("visionTheme") || "normal");

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

  // применяем класс к body
  useEffect(() => {
    document.body.classList.remove("low-vision-yellow", "low-vision-white");
    if (theme !== "normal") {
      document.body.classList.add(theme);
    }
    localStorage.setItem("visionTheme", theme);
  }, [theme]);

  // переключение по клику
  const cycleTheme = () => {
    const idx = themes.indexOf(theme);
    const next = themes[(idx + 1) % themes.length];
    setTheme(next);
  };

  // иконка в зависимости от темы
  const getThemeIcon = () => {
    switch (theme) {
      case "low-vision-yellow":
        return "🟨"; // жёлтый на чёрном
      case "low-vision-white":
        return "🌑"; // белый на чёрном
      default:
        return "🔆"; // обычная версия
    }
  };

  // горячие клавиши Alt+0..2
  useEffect(() => {
    const handleKey = (e) => {
      if (e.altKey) {
        switch (e.key) {
          case "0":
            setTheme("normal");
            break;
          case "1":
            setTheme("low-vision-yellow");
            break;
          case "2":
            setTheme("low-vision-white");
            break;
          default:
            break;
        }
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    navigate("/");
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setShowSearch(false);
      setQuery("");
    }
  };

  return (
    <header
      style={{
        background: "#111",
        borderBottom: "1px solid #333",
        position: "sticky",
        top: 0,
        zIndex: 50,
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 16px",
        }}
      >
        {/* ✅ ЛОГОТИП */}
        <Link to="/" style={{ display: "flex", alignItems: "center" }}>
          <Logo className="h-12 w-auto text-white transition-transform duration-200 hover:scale-105 hover:text-blue-500" />
        </Link>

        {/* ✅ ИКОНКИ справа */}
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          {/* 🔥 Переключатель версий иконкой */}
          <button
            onClick={cycleTheme}
            title="Переключить версию (Alt+0..2)"
            className="text-2xl cursor-pointer transition-transform duration-200 hover:scale-110"
            style={{ background: "none", border: "none", color: "white" }}
          >
            {getThemeIcon()}
          </button>

          {/* Поиск */}
          <div style={{ position: "relative" }}>
            <button
              onClick={() => setShowSearch((s) => !s)}
              className="text-white text-xl cursor-pointer transition-transform duration-200 hover:scale-110 hover:text-blue-500"
            >
              <FaSearch />
            </button>

            {showSearch && (
              <div
                style={{
                  position: "absolute",
                  top: "120%",
                  right: 0,
                  background: "#111",
                  border: "1px solid #333",
                  borderRadius: 8,
                  padding: 8,
                  width: 280,
                  boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
                  animation: "fadeIn 0.2s ease",
                  display: "flex",
                  gap: 6,
                }}
              >
                <form
                  onSubmit={handleSearchSubmit}
                  style={{ display: "flex", gap: 6, width: "100%" }}
                >
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Поиск..."
                    autoFocus
                    style={{
                      flex: 1,
                      padding: "6px 10px",
                      borderRadius: 6,
                      border: "1px solid #444",
                      background: "#222",
                      color: "white",
                      fontSize: 14,
                    }}
                  />
                  <button
                    type="submit"
                    style={{
                      background: "#1a73e8",
                      color: "white",
                      border: "none",
                      borderRadius: 6,
                      padding: "0 12px",
                      cursor: "pointer",
                      fontSize: 14,
                    }}
                  >
                    Найти
                  </button>
                </form>
              </div>
            )}
          </div>

          {/* Бургер */}
          <button
            onClick={() => setMenuOpen(true)}
            className="text-white text-2xl cursor-pointer transition-transform duration-200 hover:scale-110 hover:text-blue-500"
          >
            <FaBars />
          </button>
        </div>
      </div>

      {/* Оверлей */}
      {menuOpen && (
        <div
          onClick={() => setMenuOpen(false)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background: "rgba(0,0,0,0.6)",
            zIndex: 90,
            transition: "opacity 0.3s ease",
          }}
        />
      )}

      {/* Меню (Сайдбар) */}
      <div
        className="sidebar-menu"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          width: 260,
          height: "100%",
          padding: 16,
          boxShadow: "-2px 0 8px rgba(0,0,0,0.5)",
          zIndex: 100,
          display: "flex",
          flexDirection: "column",
          gap: 12,
          transform: menuOpen ? "translateX(0)" : "translateX(100%)",
          transition: "transform 0.3s ease",
        }}
      >
        {/* Крестик */}
        <button
          onClick={() => setMenuOpen(false)}
          className="close-btn text-xl cursor-pointer transition-transform duration-200 hover:scale-110 mb-3"
        >
          <FaTimes />
        </button>

        <Link to="/" onClick={() => setMenuOpen(false)}>Главная</Link>
        <Link to="/categories" onClick={() => setMenuOpen(false)}>Категории</Link>

        {user ? (
          <>
            <Link to="/author" onClick={() => setMenuOpen(false)}>Личный кабинет</Link>
            <button
              onClick={handleLogout}
              style={{
                background: "none",
                border: "none",
                textAlign: "left",
                cursor: "pointer",
                padding: 0,
              }}
            >
              Выйти
            </button>
          </>
        ) : (
          <Link to="/login" onClick={() => setMenuOpen(false)}>Войти</Link>
        )}
      </div>
    </header>
  );
}
