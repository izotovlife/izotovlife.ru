// frontend/src/components/Favorites.js
// Компонент отображения избранных новостей пользователя.

import React, { useEffect, useState } from "react";
import api from "../api";

function Favorites() {
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    async function loadFavorites() {
      try {
        const res = await api.get("news/favorites/");
        setFavorites(res.data);
      } catch (err) {
        console.error("Ошибка загрузки избранного:", err);
      }
    }
    loadFavorites();
  }, []);

  return (
    <div className="container">
      {favorites.map((fav) => (
        <div key={fav.id} className="card">
          {fav.news.image && (
            <div className="card-image">
              <img src={fav.news.image} alt={fav.news.title} />
            </div>
          )}
          <div className="card-content">
            <span className="card-title">
              <a href={fav.news.link} target="_blank" rel="noopener noreferrer">
                {fav.news.title}
              </a>
            </span>
            <p>{fav.news.content?.slice(0, 150)}...</p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default Favorites;

