// frontend/src/components/Popular.js
// Путь: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\frontend\src\components\Popular.js
// Назначение: компонент для отображения популярных новостей.
// Исправлено: добавлен useCallback для загрузки данных и корректные зависимости в useEffect.

import React, { useEffect, useState, useCallback } from "react";
import api from "../api";

function Popular() {
  const [popular, setPopular] = useState([]);
  const isLoggedIn = !!localStorage.getItem("access");

  const addFavorite = async (id) => {
    try {
      await api.post(`news/favorites/${id}/`);
    } catch (err) {
      console.error("Ошибка добавления в избранное:", err);
    }
  };

  const loadPopular = useCallback(async () => {
    try {
      const res = await api.get("news/popular/");
      setPopular(res.data);
    } catch (err) {
      console.error("Ошибка загрузки популярных новостей:", err);
    }
  }, []);

  useEffect(() => {
    loadPopular();
  }, [loadPopular]);

  return (
    <div className="container">
      <h4>Популярное</h4>
      <div className="row">
        {popular.map((n, index) => (
          <div key={`${n.id}-${index}`} className="col s12 m6 l4">
            <div className="card">
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
                {isLoggedIn && (
                  <button className="btn" onClick={() => addFavorite(n.id)}>
                    В избранное
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Popular;
