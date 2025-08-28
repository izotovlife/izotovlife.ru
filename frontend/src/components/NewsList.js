// ===== ФАЙЛ: frontend/src/components/NewsList.js =====
// ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\frontend\\src\\components\\NewsList.js
// НАЗНАЧЕНИЕ: Лента новостей с поиском, фильтрацией по категориям и ленивой подгрузкой.
// ОПИСАНИЕ: Использует Materialize CSS для карточек новостей.

import React, { useEffect, useState, useCallback } from "react";
import api from "../api";

function NewsList() {
  const [news, setNews] = useState([]);
  const [categories, setCategories] = useState([]);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");

  const loadCategories = useCallback(async () => {
    try {
      const res = await api.get("news/categories/");
      setCategories(res.data);
    } catch (err) {
      console.error("Ошибка загрузки категорий:", err);
    }
  }, []);

  const loadNews = useCallback(async () => {
    try {
      const params = { page };
      if (search) params.search = search;
      if (category) params.category = category;
      const res = await api.get("news/", { params });
      setNews((prev) => [...prev, ...res.data.results]);
    } catch (err) {
      console.error("Ошибка загрузки новостей:", err);
    }
  }, [page, search, category]);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

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

  const handleSearchChange = (e) => {
    setNews([]);
    setPage(1);
    setSearch(e.target.value);
  };

  const handleCategoryChange = (e) => {
    setNews([]);
    setPage(1);
    setCategory(e.target.value);
  };

  return (
    <div className="container">
      <div className="row">
        <div className="input-field col s12 m6">
          <input
            id="search"
            type="text"
            value={search}
            onChange={handleSearchChange}
          />
          <label htmlFor="search" className={search ? "active" : ""}>
            Поиск
          </label>
        </div>
        <div className="input-field col s12 m6">
          <select
            value={category}
            onChange={handleCategoryChange}
            className="browser-default"
          >
            <option value="">Все категории</option>
            {categories.map((c) => (
              <option key={c.id} value={c.slug}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

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
            {n.content && <p>{n.content.slice(0, 150)}...</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

export default NewsList;
