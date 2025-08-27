// frontend/src/components/NewsList.js
import React, { useEffect, useState, useCallback } from "react";
import api from "../api";

function NewsList() {
  const [news, setNews] = useState([]);
  const [page, setPage] = useState(1);

  const loadNews = useCallback(async () => {
    try {
      const res = await api.get(`news/?page=${page}`);
      setNews((prev) => [...prev, ...res.data.results]);
    } catch (err) {
      console.error("Ошибка загрузки новостей:", err);
    }
  }, [page]);

  useEffect(() => {
    loadNews();
  }, [loadNews]);

  const handleScroll = useCallback(() => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 2) {
      setPage((p) => p + 1);
    }
  }, []);

  useEffect(() => {
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  return (
    <div className="container">
      {news.map((n, index) => (
        <div key={`${n.id}-${index}`} className="card">
          {n.image && (
            <div className="card-image">
              <img src={n.image} alt={n.title} />
            </div>
          )}
          <div className="card-content">
            <span className="card-title">
              <a href={n.link} target="_blank" rel="noopener noreferrer">
                {n.title}
              </a>
            </span>
            <p>{n.content?.slice(0, 150)}...</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default NewsList;
