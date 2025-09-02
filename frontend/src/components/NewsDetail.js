// frontend/src/components/NewsDetail.js
// Компонент для отображения полной новости по клику

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

function NewsDetail() {
  const { id } = useParams(); // получаем id из URL
  const [news, setNews] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/news/${id}/`)
      .then((res) => res.json())
      .then((data) => {
        setNews(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="card">Загрузка...</div>;
  if (!news) return <div className="card">Новость не найдена</div>;

  return (
    <div className="news-detail">
      <h1>{news.title}</h1>
      {news.image && (
        <img src={news.image} alt={news.title} className="news-detail-image" />
      )}
      <p className="news-detail-text">{news.content}</p>
      {news.author && (
        <p className="news-meta">Автор: {news.author}, {news.date}</p>
      )}
    </div>
  );
}

export default NewsDetail;
