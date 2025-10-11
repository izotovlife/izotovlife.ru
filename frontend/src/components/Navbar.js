// Путь: frontend/src/components/Navbar.js
// Назначение: фиксированная шапка IzotovLife с логотипом, погодой, валютами,
// поиском, категориями и боковым меню.
// Обновлено:
//   ✅ Удалён пункт "Главная" из бокового меню (логотип и так ведёт на /).
//   ✅ "Категории" ведёт на страницу /categories.
//   ✅ Добавлен "Регистрация" для неавторизованных пользователей.

import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { whoami, setToken, goToAdmin, fetchCategories } from "../Api";
import {
  FaSearch,
  FaBars,
  FaTimes,
  FaChevronDown,
  FaEye,
} from "react-icons/fa";
import { ReactComponent as Logo } from "../assets/izotovlife_logo.svg";
import SuggestNewsModal from "./SuggestNewsModal";
import WeatherWidget from "./WeatherWidget";
import SearchAutocomplete from "./search/SearchAutocomplete";
import "./Navbar.css";

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [openSuggest, setOpenSuggest] = useState(false);
  const [rates, setRates] = useState({});
  const [showDropdown, setShowDropdown] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "default");
  const [categories, setCategories] = useState([]);
  const navigate = useNavigate();
  const popoverRef = useRef(null);

  // ---------------- Категории ----------------
  useEffect(() => {
    async function loadCategories() {
      try {
        const resp = await fetchCategories();
        console.log("📂 Категории из API:", resp);
        setCategories(resp);
      } catch (e) {
        console.error("Ошибка загрузки категорий:", e);
      }
    }
    loadCategories();
  }, []);

  const catArray = Array.isArray(categories)
    ? categories
    : Array.isArray(categories.results)
    ? categories.results
    : [];

  const mainCategories = catArray.slice(0, 7);
  const extraCategories = catArray.slice(7, 20);

  // ---------------- Пользователь ----------------
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

  const handlePersonalCabinet = async () => {
    if (!user) {
      navigate("/login");
      return;
    }
    if (user.is_superuser) {
      await goToAdmin();
    } else if (user.role === "EDITOR") {
      navigate("/editor-dashboard");
    } else {
      navigate("/author-dashboard");
    }
    setMenuOpen(false);
  };

  // ---------------- Курсы валют ----------------
  useEffect(() => {
    async function fetchRates() {
      try {
        const resp = await fetch("https://open.er-api.com/v6/latest/RUB");
        const data = await resp.json();
        if (data && data.rates) setRates(data.rates);
      } catch (e) {
        console.error("Ошибка загрузки курсов валют", e);
      }
    }
    fetchRates();
  }, []);

  const renderCurrency = () => {
    if (!rates || Object.keys(rates).length === 0) return "Загрузка...";
    const usd = rates["USD"] ? (1 / rates["USD"]).toFixed(2) : "...";
    const eur = rates["EUR"] ? (1 / rates["EUR"]).toFixed(2) : "...";
    return (
      <>
        <span>USD: {usd} ₽</span>
        <span>| EUR: {eur} ₽</span>
      </>
    );
  };

  // ---------------- Темы ----------------
  const applyTheme = (newTheme) => {
    document.body.classList.remove("theme-default", "theme-yellow", "theme-white");
    document.body.classList.add(`theme-${newTheme}`);
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
  };

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    const handleKey = (e) => {
      if (!e.altKey) return;
      if (e.code === "Digit0") applyTheme("default");
      if (e.code === "Digit1") applyTheme("yellow");
      if (e.code === "Digit2") applyTheme("white");
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  // ---------------- Закрытие поиска ----------------
  useEffect(() => {
    const onDocClick = (e) => {
      if (
        showSearch &&
        popoverRef.current &&
        !popoverRef.current.contains(e.target)
      ) {
        setShowSearch(false);
      }
    };
    const onEsc = (e) => {
      if (e.key === "Escape") setShowSearch(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onEsc);
    };
  }, [showSearch]);

  // ===================================================
  //                     РЕНДЕР
  // ===================================================

  return (
    <header className="navbar">
      {/* ---------- ВЕРХ ---------- */}
      <div className="navbar-top">
        <span className="navbar-logo" onClick={() => navigate("/")}>
          <Logo className="logo-svg" />
        </span>

        <div className="navbar-center">
          <div className="rates">{renderCurrency()}</div>
          <div className="weather">
            <WeatherWidget />
          </div>
        </div>

        <div className="navbar-right">
          <div className="search-anchor" ref={popoverRef}>
            <button
              className="icon-btn"
              title="Поиск"
              onClick={() => setShowSearch((v) => !v)}
            >
              <FaSearch />
            </button>

            {showSearch && (
              <div className="search-popover open">
                <button
                  className="close-search"
                  onClick={() => setShowSearch(false)}
                  aria-label="Закрыть поиск"
                >
                  <FaTimes />
                </button>
                <SearchAutocomplete />
              </div>
            )}
          </div>

          <span className="suggest-link" onClick={() => setOpenSuggest(true)}>
            Предложить новость
          </span>

          <button
            className="icon-btn"
            title="Версия для слабовидящих (Alt+0/1/2)"
            onClick={() => {
              const next =
                theme === "default"
                  ? "yellow"
                  : theme === "yellow"
                  ? "white"
                  : "default";
              applyTheme(next);
            }}
          >
            <FaEye />
          </button>

          <button
            className="icon-btn"
            title="Меню"
            onClick={() => setMenuOpen(true)}
          >
            <FaBars />
          </button>
        </div>
      </div>

      {/* ---------- КАТЕГОРИИ (в шапке) ---------- */}
      <nav className="navbar-categories">
        <div className="categories-center">
          {mainCategories.map((cat) => (
            <span
              key={cat.slug}
              className="cat-link"
              onClick={() => navigate(`/${cat.slug}/`)}
            >
              {cat.name}
            </span>
          ))}

          {extraCategories.length > 0 && (
            <div
              className="cat-dropdown"
              onMouseEnter={() => setShowDropdown(true)}
              onMouseLeave={() => setShowDropdown(false)}
            >
              <span className="cat-link dropdown-trigger">
                Ещё <FaChevronDown style={{ fontSize: "0.7em" }} />
              </span>
              {showDropdown && (
                <div className="dropdown-menu">
                  {extraCategories.map((cat) => (
                    <span
                      key={cat.slug}
                      className="dropdown-item"
                      onClick={() => {
                        setShowDropdown(false);
                        navigate(`/${cat.slug}/`);
                      }}
                    >
                      {cat.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </nav>

      {/* ---------- Боковое меню ---------- */}
      {menuOpen && (
        <>
          <div className="overlay" onClick={() => setMenuOpen(false)} />
          <div className="side-menu">
            <button className="close-btn" onClick={() => setMenuOpen(false)}>
              <FaTimes />
            </button>

            <span
              className="menu-item"
              onClick={() => {
                setMenuOpen(false);
                navigate("/categories");
              }}
            >
              Категории
            </span>

            {!user && (
              <>
                <span
                  className="menu-item"
                  onClick={() => {
                    setMenuOpen(false);
                    navigate("/login");
                  }}
                >
                  Войти
                </span>
                <span
                  className="menu-item"
                  onClick={() => {
                    setMenuOpen(false);
                    navigate("/register");
                  }}
                >
                  Регистрация
                </span>
              </>
            )}

            {user && (
              <>
                <span
                  className="menu-item"
                  onClick={() => {
                    setMenuOpen(false);
                    handlePersonalCabinet();
                  }}
                >
                  Личный кабинет
                </span>
                <span
                  className="menu-item"
                  onClick={() => {
                    handleLogout();
                    setMenuOpen(false);
                  }}
                >
                  Выйти
                </span>
              </>
            )}
          </div>
        </>
      )}

      {/* ---------- Модалка "Предложить новость" ---------- */}
      <SuggestNewsModal
        open={openSuggest}
        onClose={() => setOpenSuggest(false)}
      />
    </header>
  );
}
