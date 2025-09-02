// frontend/src/components/CategoryNews.js
// Новости по выбранной категории

import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";

function CategoryNews() {
  const { slug } = useParams();
  const [news, setNews] = useState([]);

  useEffect(() => {
    fetch(`/api/news/category/${slug}/`)
      .then(res => res.json())
      .then(data => setNews(data))
      .catch(() => setNews([]));
  }, [slug]);

  if (!news.length) {
    return <p>Нет новостей в этой категории.</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Новости категории: {slug}</h1>
      <div className="popular-grid">
        {news.map(item => (
          <div key={item.id} className="popular-card">
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

export default CategoryNews;
