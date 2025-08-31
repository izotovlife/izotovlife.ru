// frontend/src/components/Currency.js
// Виджет курсов валют
import React, { useEffect, useState } from "react";

function Currency() {
  const [rates, setRates] = useState(null);

  useEffect(() => {
    fetch("/api/news/currency/")
      .then(res => res.json())
      .then(data => setRates(data))
      .catch(() => setRates(null));
  }, []);

  if (!rates) return <div className="card">Загрузка курсов...</div>;
  if (rates.error) return <div className="card">Ошибка: {rates.error}</div>;

  return (
    <div className="card">
      <h2 className="font-semibold mb-2">Курсы валют</h2>
      <p>USD: {rates.USD} ₽</p>
      <p>EUR: {rates.EUR} ₽</p>
    </div>
  );
}

export default Currency;
