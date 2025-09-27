// frontend/src/components/HeaderInfo.js
// Назначение: Блок с курсами валют и погодой по геолокации или выбранному вручную городу.
// Обновления:
//   - Добавлен выпадающий список городов для ручного выбора.
//   - Выбор сохраняется в localStorage.
//   - Если пользователь не выбрал город, используется геолокация.
// Путь: frontend/src/components/HeaderInfo.js

import React, { useEffect, useState } from "react";

export default function HeaderInfo() {
  const [rates, setRates] = useState({});
  const [selectedCurrency, setSelectedCurrency] = useState("USD");

  const [weather, setWeather] = useState(null);
  const [selectedCity, setSelectedCity] = useState(
    localStorage.getItem("selectedCity") || ""
  );

  const cities = [
    { name: "Москва", lat: 55.7558, lon: 37.6176 },
    { name: "Санкт-Петербург", lat: 59.9343, lon: 30.3351 },
    { name: "Казань", lat: 55.7963, lon: 49.1088 },
    { name: "Новосибирск", lat: 55.0084, lon: 82.9357 },
    { name: "Екатеринбург", lat: 56.8389, lon: 60.6057 },
  ];

  // Загружаем курсы валют
  useEffect(() => {
    async function fetchRates() {
      try {
        const res = await fetch("https://api.exchangerate.host/latest?base=RUB");
        const data = await res.json();
        setRates(data.rates);
      } catch (err) {
        console.error("Ошибка загрузки курсов валют:", err);
      }
    }
    fetchRates();
  }, []);

  // Функция загрузки погоды
  async function loadWeather(lat, lon, cityName = "") {
    try {
      const API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"; // 🔑 вставь сюда свой ключ
      const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=metric&lang=ru&appid=${API_KEY}`;
      const res = await fetch(url);
      const data = await res.json();
      setWeather({
        temp: data.main.temp,
        pressure: data.main.pressure,
        city: cityName || data.name,
      });
    } catch (err) {
      console.error("Ошибка загрузки погоды:", err);
    }
  }

  // Если выбран город вручную
  useEffect(() => {
    if (selectedCity) {
      const cityObj = cities.find((c) => c.name === selectedCity);
      if (cityObj) {
        loadWeather(cityObj.lat, cityObj.lon, cityObj.name);
      }
    } else {
      // Автоопределение по геолокации
      if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            loadWeather(pos.coords.latitude, pos.coords.longitude);
          },
          (err) => {
            console.warn("Геолокация отклонена:", err);
          }
        );
      }
    }
  }, [selectedCity]);

  // Сохраняем выбор города
  const handleCityChange = (e) => {
    const city = e.target.value;
    setSelectedCity(city);
    localStorage.setItem("selectedCity", city);
  };

  return (
    <div className="flex items-center gap-6 text-sm text-gray-200 px-4 py-2 bg-[#111827]">
      {/* Валюты */}
      <div className="flex items-center gap-2">
        <span>Курс:</span>
        <span>USD: {rates["USD"] ? (1 / rates["USD"]).toFixed(2) : "..."}</span>
        <span>EUR: {rates["EUR"] ? (1 / rates["EUR"]).toFixed(2) : "..."}</span>
        <select
          value={selectedCurrency}
          onChange={(e) => setSelectedCurrency(e.target.value)}
          className="bg-[#0b132b] text-white rounded px-1 py-0.5 ml-2"
        >
          {Object.keys(rates).map((cur) => (
            <option key={cur} value={cur}>
              {cur}
            </option>
          ))}
        </select>
        {selectedCurrency !== "USD" && selectedCurrency !== "EUR" && (
          <span>
            {selectedCurrency}:{" "}
            {rates[selectedCurrency]
              ? (1 / rates[selectedCurrency]).toFixed(2)
              : "..."}
          </span>
        )}
      </div>

      {/* Погода */}
      <div className="flex items-center gap-2">
        <select
          value={selectedCity}
          onChange={handleCityChange}
          className="bg-[#0b132b] text-white rounded px-1 py-0.5"
        >
          <option value="">Мой город (авто)</option>
          {cities.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </select>
        {weather && (
          <div>
            {weather.city}: {weather.temp.toFixed(1)}°C, Давл. {weather.pressure} мм рт. ст.
          </div>
        )}
      </div>
    </div>
  );
}
