// ===== ФАЙЛ: frontend/src/components/NewsList.js =====
// ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\frontend\\src\\components\\NewsList.js
// НАЗНАЧЕНИЕ: Лента новостей с поиском, вкладками категорий и ленивой подгрузкой.
// ОПИСАНИЕ: Показывает карточки новостей с изображением, заголовком и ссылкой.

import React, { useEffect, useState, useCallback } from "react";
import api from "../api";
import CategoryTabs from "./CategoryTabs";

function NewsList() {
  const [news, setNews] = useState([]);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");

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

  const handleCategorySelect = (slug) => {
    setNews([]);
    setPage(1);
    setCategory(slug);
  };

  return (
    <div className="container">
      <div className="row">
        <div className="input-field col s12">
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
      </div>

      <CategoryTabs active={category} onSelect={handleCategorySelect} />

      <div className="row">
        {news.map((n, index) => (
          <div key={`${n.id}-${index}`} className="col s12 m6 l4">
            <div className="card hoverable">
              {n.image && (
                  <div className="card-image">
                    <img className="responsive-img" src={n.image} alt={n.title} />
                  </div>
              )}
              <div className="card-content">
                <span className="card-title truncate">{n.title}</span>
                {n.content && <p>{n.content.slice(0, 100)}...</p>}
              </div>
              <div className="card-action">
                <a href={n.link} target="_blank" rel="noopener noreferrer">
                  Читать далее
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default NewsList;
