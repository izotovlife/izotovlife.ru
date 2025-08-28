// ===== ФАЙЛ: frontend/src/components/CategoryTabs.js =====
// ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\frontend\\src\\components\\CategoryTabs.js
// НАЗНАЧЕНИЕ: Горизонтальные вкладки категорий новостей.
// ОПИСАНИЕ: Загружает список категорий с backend и позволяет выбирать
//            разделы через вкладки Materialize CSS.

import React, { useEffect, useState } from "react";
import M from "materialize-css";
import api from "../api";

function CategoryTabs({ active, onSelect }) {
  const [categories, setCategories] = useState([]);

  // Загружаем категории один раз при монтировании
  useEffect(() => {
    async function fetchCategories() {
      try {
        const res = await api.get("news/categories/");
        setCategories(res.data);
      } catch (err) {
        console.error("Ошибка загрузки категорий:", err);
      }
    }
    fetchCategories();
  }, []);

  // Инициализируем вкладки после загрузки категорий
  useEffect(() => {
    const elems = document.querySelectorAll(".tabs");
    M.Tabs.init(elems);
  }, [categories]);

  const handleClick = (slug) => (e) => {
    e.preventDefault();
    onSelect(slug);
  };

  return (
    <div className="row">
        <div className="col s12">
          <ul className="tabs">
          <li className="tab" key="all">
            <a
              href="#!"
              className={active === "" ? "active" : ""}
              onClick={handleClick("")}
            >
              Все
            </a>
          </li>
          {categories.map((c) => (
            <li className="tab" key={c.id}>
              <a
                href="#!"
                className={active === c.slug ? "active" : ""}
                onClick={handleClick(c.slug)}
              >
                {c.name}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default CategoryTabs;
