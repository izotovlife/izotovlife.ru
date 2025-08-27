// frontend/src/components/Moderation.js
// Путь: frontend/src/components/Moderation.js
// Назначение: интерфейс редактора для модерации новостей.

import React, { useEffect, useState } from "react";
import api from "../api";

function Moderation() {
  const [items, setItems] = useState([]);

  const loadItems = async () => {
    try {
      const res = await api.get("news/moderation/");
      setItems(res.data);
    } catch (err) {
      console.error("Ошибка загрузки:", err);
    }
  };

  useEffect(() => {
    loadItems();
  }, []);

  const approve = async (id) => {
    try {
      await api.post(`news/moderation/${id}/approve/`);
      setItems((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      console.error("Ошибка одобрения:", err);
    }
  };

  return (
    <div className="container">
      <h4>Модерация новостей</h4>
      {items.map((n) => (
        <div key={n.id} className="card">
          <div className="card-content">
            <span className="card-title">{n.title}</span>
            <p>{n.content?.slice(0, 150)}...</p>
            <button className="btn" onClick={() => approve(n.id)}>
              Одобрить
            </button>
          </div>
        </div>
      ))}
      {items.length === 0 && <p>Нет новостей для модерации.</p>}
    </div>
  );
}

export default Moderation;
