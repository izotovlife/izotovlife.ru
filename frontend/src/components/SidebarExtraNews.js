// frontend/src/components/SidebarExtraNews.js
// Правая колонка (дополнительные текстовые новости)
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function SidebarExtraNews() {
  const [news, setNews] = useState([]);

  useEffect(() => {
    fetch("/api/news/short/") // можно сделать отдельный эндпоинт /api/news/extra/
      .then(res => res.json())
      .then(data => setNews(data))
      .catch(() => setNews([]));
  }, []);

  return (
    <aside className="card text-sm">
      <h2 className="font-semibold mb-2">Новости</h2>
      <ul className="space-y-1">
        {news.map(item => (
          <li key={item.id}>
            <Link to={`/news/${item.id}`} className="hover:underline block">
              {item.title}
            </Link>
          </li>
        ))}
      </ul>
    </aside>
  );
}

export default SidebarExtraNews;
