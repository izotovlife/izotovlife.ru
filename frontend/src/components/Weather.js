// frontend/src/components/Weather.js
// Виджет погоды
import React, { useEffect, useState } from "react";

function Weather() {
  const [weather, setWeather] = useState(null);

  useEffect(() => {
    fetch("/api/news/weather/") // эндпоинт бэкенда
      .then(res => res.json())
      .then(data => setWeather(data))
      .catch(() => setWeather(null));
  }, []);

  if (!weather) return <div className="card">Загрузка погоды...</div>;
  if (weather.error) return <div className="card">Ошибка: {weather.error}</div>;

  return (
    <div className="card">
      <h2 className="font-semibold mb-2">Погода</h2>
      <p>{weather.city}: {weather.temp}°C, {weather.description}</p>
    </div>
  );
}

export default Weather;
