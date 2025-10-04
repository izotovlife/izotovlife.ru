// frontend/src/components/Navbar.js
// Назначение: фиксированная шапка (логотип, меню, поиск с выпадающими подсказками,
// переключатель слабовидящих, блок с курсами валют и погодой по геолокации пользователя).
// Теперь добавлен автокомплит: первые 5 найденных новостей выпадают прямо под поиском
// и кликабельны (Link для внутренних статей, <a> для RSS).

import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { whoami, setToken, goToAdmin, searchAll } from "../Api";
import { FaSearch, FaBars, FaTimes } from "react-icons/fa";
import { ReactComponent as Logo } from "../assets/izotovlife_logo.svg";

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]); // результаты для выпадашки
  const [user, setUser] = useState(null);

  // валюты
  const [rates, setRates] = useState({});
  const [selectedCurrency, setSelectedCurrency] = useState("USD+EUR");

  // геолокация + погода
  const [coords, setCoords] = useState(null);
  const [weather, setWeather] = useState(null);

  // темы для слабовидящих
  const themes = ["normal", "low-vision-yellow", "low-vision-white"];
  const [theme, setTheme] = useState(
    localStorage.getItem("visionTheme") || "normal"
  );

  const navigate = useNavigate();

  // Загружаем пользователя
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

  // переключение темы
  const cycleTheme = () => {
    const idx = themes.indexOf(theme);
    const next = themes[(idx + 1) % themes.length];
    setTheme(next);
  };

  // иконка темы
  const getThemeIcon = () => {
    switch (theme) {
      case "low-vision-yellow":
        return "🟨";
      case "low-vision-white":
        return "🌑";
      default:
        return "🔆";
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

  // выход
  const handleLogout = () => {
    setToken(null);
    setUser(null);
    navigate("/");
  };

  // поиск по кнопке "Найти"
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setShowSearch(false);
      setQuery("");
      setResults([]);
    }
  };

  // автокомплит: загрузка первых 5 результатов
  useEffect(() => {
    let active = true;
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        const data = await searchAll(query.trim(), { limit: 5, offset: 0 });
        if (active) setResults(data.items || []);
      } catch {
        if (active) setResults([]);
      }
    }, 300);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [query]);

  // Личный кабинет
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

  // Загружаем курсы валют
  useEffect(() => {
    async function fetchRates() {
      try {
        const resp = await fetch("https://open.er-api.com/v6/latest/RUB");
        const data = await resp.json();
        if (data && data.rates) {
          setRates(data.rates);
        }
      } catch (e) {
        console.error("Ошибка загрузки курсов валют", e);
      }
    }
    fetchRates();
  }, []);

  // Определяем координаты
  useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
          });
        },
        (err) => console.warn("Ошибка геолокации", err),
        { enableHighAccuracy: true }
      );
    }
  }, []);

  // Загружаем погоду
  useEffect(() => {
    if (!coords) return;

    async function fetchWeather() {
      try {
        const resp = await fetch(
          `https://wttr.in/${coords.lat},${coords.lon}?format=j1&lang=ru`
        );
        const data = await resp.json();

        const cond = data.current_condition[0];
        const pressureMmHg = Math.round(cond.pressure * 0.75006); // перевод hPa → мм рт. ст.

        setWeather({
          area: data.nearest_area[0].areaName[0].value, // город на русском
          temp: cond.temp_C,
          desc: cond.lang_ru[0].value, // описание на русском
          pressure: pressureMmHg,
        });
      } catch (e) {
        console.error("Ошибка погоды", e);
      }
    }

    fetchWeather();
  }, [coords]);

  // Рендерим валюты
  const renderCurrency = () => {
    if (!rates || Object.keys(rates).length === 0) return "Загрузка...";

    if (selectedCurrency === "USD+EUR") {
      const usd = (1 / rates["USD"]).toFixed(2);
      const eur = (1 / rates["EUR"]).toFixed(2);
      return `USD: ${usd} ₽ | EUR: ${eur} ₽`;
    } else {
      const val = selectedCurrency;
      const rate = rates[val] ? (1 / rates[val]).toFixed(2) : "...";
      return `${val}: ${rate} ₽`;
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
          maxWidth: 1400,
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 16px",
          flexWrap: "wrap",
          gap: "10px",
        }}
      >
        {/* ЛОГОТИП */}
        <Link to="/" style={{ display: "flex", alignItems: "center" }}>
          <Logo className="h-12 w-auto text-white transition-transform duration-200 hover:scale-105 hover:text-blue-500" />
        </Link>

        {/* Блок с курсами валют и погодой */}
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "20px",
            color: "white",
            fontSize: "14px",
          }}
        >
          <div>{renderCurrency()}</div>
          <select
            value={selectedCurrency}
            onChange={(e) => setSelectedCurrency(e.target.value)}
            style={{
              background: "#111",
              color: "white",
              border: "1px solid #444",
              borderRadius: 4,
              padding: "2px 6px",
            }}
          >
            <option value="USD+EUR">Доллар + Евро</option>
            <option value="USD">Доллар</option>
            <option value="EUR">Евро</option>
            <option value="GBP">Фунт</option>
            <option value="CNY">Юань</option>
            <option value="JPY">Йена</option>
          </select>

          {/* Погода */}
          {weather && (
            <div style={{ whiteSpace: "nowrap" }}>
              <strong>{weather.area}</strong>: {weather.temp}°C, {weather.desc},
              Давл. {weather.pressure} мм рт. ст.
            </div>
          )}
        </div>

        {/* ИКОНКИ справа */}
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
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

                {/* ВЫПАДАЮЩИЕ РЕЗУЛЬТАТЫ */}
                {results.length > 0 && (
                  <ul
                    style={{
                      listStyle: "none",
                      margin: "8px 0 0",
                      padding: 0,
                      background: "#222",
                      border: "1px solid #333",
                      borderRadius: 6,
                      maxHeight: 250,
                      overflowY: "auto",
                      width: "100%",
                      zIndex: 100,
                      position: "relative",
                    }}
                  >
                    {results.map((it) => (
                      <li key={it.id || it.slug}>
                        {it.type === "rss" && it.source_url ? (
                          <a
                            href={it.source_url}
                            target="_blank"
                            rel="noreferrer"
                            style={{
                              display: "block",
                              padding: "6px 10px",
                              color: "white",
                              textDecoration: "none",
                            }}
                            onClick={() => {
                              setShowSearch(false);
                              setQuery("");
                              setResults([]);
                            }}
                          >
                            {it.title}
                          </a>
                        ) : (
                          <Link
                            to={`/news/${it.category_slug}/${it.slug}`}
                            style={{
                              display: "block",
                              padding: "6px 10px",
                              color: "white",
                              textDecoration: "none",
                            }}
                            onClick={() => {
                              setShowSearch(false);
                              setQuery("");
                              setResults([]);
                            }}
                          >
                            {it.title}
                          </Link>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
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

      {/* Сайдбар */}
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
          background: "#111",
          color: "#fff",
        }}
      >
        <button
          onClick={() => setMenuOpen(false)}
          className="close-btn text-xl cursor-pointer transition-transform duration-200 hover:scale-110 mb-3"
        >
          <FaTimes />
        </button>

        <Link to="/" onClick={() => setMenuOpen(false)}>
          Главная
        </Link>
        <Link to="/categories" onClick={() => setMenuOpen(false)}>
          Категории
        </Link>

        {user ? (
          <>
            <button
              onClick={handlePersonalCabinet}
              style={{
                background: "none",
                border: "none",
                textAlign: "left",
                cursor: "pointer",
                padding: 0,
                color: "inherit",
              }}
            >
              Личный кабинет
            </button>
            <button
              onClick={handleLogout}
              style={{
                background: "none",
                border: "none",
                textAlign: "left",
                cursor: "pointer",
                padding: 0,
                color: "inherit",
              }}
            >
              Выйти
            </button>
          </>
        ) : (
          <Link to="/login" onClick={() => setMenuOpen(false)}>
            Войти
          </Link>
        )}
      </div>
    </header>
  );
}
