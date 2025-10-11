// Путь: frontend/src/components/WeatherWidget.js
// Назначение: Виджет погоды для шапки сайта IzotovLife.
// Обновления:
//   ✅ Погода больше не пропадает при загрузке (есть placeholder).
//   ✅ Выравнивание всех элементов по центру (совместимо с Navbar).
//   ✅ Иконки 🌍 и ⟳ центрированы и не двигают строку.
//   ✅ Контейнер всегда имеет фиксированную высоту (не схлопывается).
//   ✅ Поддержка адаптива из Navbar.css.

import React, { useEffect, useRef, useState } from "react";
import "./WeatherWidget.css";

const weatherNames = {
  0: "Ясно ☀️",
  1: "Преим. ясно 🌤",
  2: "Переменная облачность ⛅",
  3: "Пасмурно ☁️",
  45: "Туман 🌫️",
  48: "Изморось 🌫️",
  51: "Морось 🌦️",
  61: "Дождь 🌧️",
  63: "Сильный дождь 🌧️",
  71: "Снег 🌨️",
  75: "Снегопад ❄️",
  80: "Кратковременный дождь 🌦️",
  81: "Ливни ⛈️",
  95: "Гроза ⚡",
  99: "Гроза с градом ⛈️",
};

export default function WeatherWidget() {
  const [city, setCity] = useState(localStorage.getItem("weatherCity") || "");
  const [suggestions, setSuggestions] = useState([]);
  const [weather, setWeather] = useState(null);
  const [fade, setFade] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [manualMode, setManualMode] = useState(false);
  const timerRef = useRef(null);
  const refreshTimerRef = useRef(null);

  // --- Определяем местоположение при загрузке ---
  useEffect(() => {
    if (!city && "geolocation" in navigator) {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          fetchWeatherByCoords(latitude, longitude, "Ваш город");
        },
        () => fetchWeatherByCity("Москва"),
        { enableHighAccuracy: true, timeout: 5000 }
      );
    } else if (city) {
      fetchWeatherByCity(city);
    } else {
      fetchWeatherByCity("Москва");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Подсказки при ручном вводе ---
  useEffect(() => {
    if (!manualMode || !city || city.length < 2) {
      setSuggestions([]);
      return;
    }
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
            city
          )}&count=5&language=ru`
        );
        const data = await res.json();
        setSuggestions(data.results || []);
      } catch {}
    }, 300);
    return () => clearTimeout(timerRef.current);
  }, [city, manualMode]);

  // --- Автообновление каждые 15 минут ---
  useEffect(() => {
    if (!city) return;
    if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
    refreshTimerRef.current = setInterval(() => {
      fetchWeatherByCity(city);
    }, 15 * 60 * 1000);
    return () => clearInterval(refreshTimerRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [city]);

  // --- Погода по координатам ---
  async function fetchWeatherByCoords(lat, lon, name) {
    try {
      setLoading(true);
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weathercode,surface_pressure&timezone=auto`;
      const resp = await fetch(url);
      const data = await resp.json();
      const cur = data.current;
      if (!cur) return;
      const desc = weatherNames[cur.weathercode] || "Неизвестно";

      setFade(false);
      setTimeout(() => {
        setWeather({
          area: name,
          temp: Math.round(cur.temperature_2m),
          desc,
          pressure: Math.round(cur.surface_pressure * 0.75006),
        });
        setFade(true);
        setLoading(false);
        setLastUpdated(new Date());
      }, 100);

      localStorage.setItem("weatherCity", name);
      setManualMode(false);
    } catch (e) {
      console.error("Ошибка погоды:", e);
      setLoading(false);
    }
  }

  // --- Погода по названию города ---
  async function fetchWeatherByCity(cityName) {
    try {
      setLoading(true);
      const res = await fetch(
        `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
          cityName
        )}&count=1&language=ru`
      );
      const geo = await res.json();
      if (!geo.results || !geo.results[0]) {
        setLoading(false);
        return;
      }
      const { latitude, longitude, name } = geo.results[0];
      await fetchWeatherByCoords(latitude, longitude, name);
    } catch (e) {
      console.error("Ошибка определения города:", e);
      setLoading(false);
    }
  }

  const formatTime = (d) =>
    d ? d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" }) : "";

  return (
    <div className="weather-widget">
      {/* Кнопки выбора и обновления */}
      <button
        onClick={() => setManualMode((m) => !m)}
        title="Выбрать город вручную"
        style={{
          background: "none",
          border: "none",
          color: "white",
          cursor: "pointer",
          fontSize: 18,
        }}
      >
        🌍
      </button>

      <button
        onClick={() => fetchWeatherByCity(city || "Москва")}
        title="Обновить погоду"
        className={loading ? "rotate-icon" : ""}
        style={{
          background: "none",
          border: "none",
          color: "white",
          cursor: "pointer",
          fontSize: 16,
        }}
      >
        ⟳
      </button>

      {/* Основной блок с погодой (всегда виден) */}
      <div className={`weather-fade ${fade ? "fade-in" : ""}`}>
        {weather ? (
          <>
            <span className="weather-city">
              <strong>{weather.area}</strong>:
            </span>
            <span className="weather-temp">{weather.temp}°C</span>
            <span className="weather-desc">{weather.desc}</span>
            <span className="weather-pressure">
              Давл. {weather.pressure} мм рт. ст.
            </span>
            {lastUpdated && (
              <span className="weather-time" style={{ fontSize: 12, color: "#bbb" }}>
                Обновлено: {formatTime(lastUpdated)}
              </span>
            )}
          </>
        ) : (
          <span style={{ color: "#bbb" }}>Загрузка погоды...</span>
        )}
      </div>

      {/* Поле ручного ввода города */}
      {manualMode && (
        <div style={{ position: "relative", marginTop: 6 }}>
          <input
            value={city}
            placeholder="Введите город..."
            onChange={(e) => setCity(e.target.value)}
            style={{
              background: "#111",
              color: "white",
              border: "1px solid #444",
              borderRadius: 6,
              padding: "4px 8px",
              width: 180,
            }}
            autoFocus
          />
          {suggestions.length > 0 && (
            <div
              style={{
                position: "absolute",
                top: "110%",
                left: 0,
                background: "#0f1115",
                border: "1px solid #333",
                borderRadius: 8,
                zIndex: 30,
                width: "100%",
                boxShadow: "0 4px 8px rgba(0,0,0,0.4)",
              }}
            >
              {suggestions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => {
                    setCity(s.name);
                    fetchWeatherByCoords(s.latitude, s.longitude, s.name);
                    setSuggestions([]);
                  }}
                  style={{
                    padding: "6px 10px",
                    cursor: "pointer",
                    fontSize: 14,
                  }}
                  onMouseDown={(e) => e.preventDefault()}
                  onMouseOver={(e) =>
                    (e.currentTarget.style.background = "#1a1a1a")
                  }
                  onMouseOut={(e) =>
                    (e.currentTarget.style.background = "transparent")
                  }
                >
                  {s.name} {s.country ? `(${s.country})` : ""}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
