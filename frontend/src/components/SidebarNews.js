// frontend/src/components/SidebarNews.js
// Левая колонка: список коротких новостей
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function SidebarNews() {
  const [news, setNews] = useState([]);

  useEffect(() => {
    fetch("/api/news/short/")
      .then(res => res.json())
      .then(data => setNews(data))
      .catch(() => setNews([]));
  }, []);

  return (
    <aside className="card text-sm">
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

export default SidebarNews;
