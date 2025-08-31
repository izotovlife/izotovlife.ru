// frontend/src/components/Popular.js
// Компонент: выводит сетку популярных новостей (без заголовка "Популярное")

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function Popular() {
  const [news, setNews] = useState([]);

  useEffect(() => {
    fetch("/api/news/popular/") // эндпоинт популярных новостей
      .then((res) => res.json())
      .then((data) => setNews(data))
      .catch(() => setNews([]));
  }, []);

  return (
    <div className="popular-block">
      {/* Заголовок удалён */}
      <div className="popular-grid">
        {news.map((item) => (
          <div className="popular-card" key={item.id}>
            {item.image && (
              <img src={item.image} alt={item.title} />
            )}
            <h3>
              <Link to={`/news/${item.id}`}>{item.title}</Link>
            </h3>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Popular;
