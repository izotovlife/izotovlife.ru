// frontend/src/components/CategoryTabs.js
// Компонент отображения категорий с кнопкой подписки.

import React, { useEffect, useState } from "react";
import api from "../api";

function CategoryTabs() {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.get("news/categories/");
        setCategories(res.data);
      } catch (err) {
        console.error("Ошибка загрузки категорий:", err);
      }
    }
    load();
  }, []);

  const handleSubscribe = async (id) => {
    try {
      await api.post(`news/categories/${id}/subscribe/`);
      alert("Подписка оформлена");
    } catch (err) {
      console.error("Ошибка подписки:", err);
    }
  };

  return (
    <div className="category-tabs">
      {categories.map((c) => (
        <div key={c.id} className="category-item">
          <span>{c.name}</span>
          <button className="btn" onClick={() => handleSubscribe(c.id)}>
            Подписаться
          </button>
        </div>
      ))}
    </div>
  );
}

export default CategoryTabs;
