// frontend/src/components/AddNews.js
// Путь: frontend/src/components/AddNews.js
// Назначение: форма для добавления новостей автором.

import React, { useEffect, useState } from "react";
import api from "../api";

function AddNews() {
  const [form, setForm] = useState({
    title: "",
    link: "",
    image: "",
    content: "",
    category: "",
  });
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    async function loadCategories() {
      try {
        const res = await api.get("news/categories/");
        setCategories(res.data);
      } catch (err) {
        console.error("Ошибка загрузки категорий:", err);
      }
    }
    loadCategories();
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post("news/create/", form);
      alert("Новость отправлена на модерацию");
      setForm({ title: "", link: "", image: "", content: "", category: "" });
    } catch (err) {
      console.error("Ошибка отправки новости:", err);
    }
  };

  return (
    <div className="container">
      <h4>Добавить новость</h4>
      <form onSubmit={handleSubmit}>
        <div className="input-field">
          <input
            id="title"
            name="title"
            value={form.title}
            onChange={handleChange}
            required
          />
          <label className="active" htmlFor="title">Заголовок</label>
        </div>

        <div className="input-field">
          <input
            id="link"
            name="link"
            value={form.link}
            onChange={handleChange}
            required
          />
          <label className="active" htmlFor="link">Ссылка на источник</label>
        </div>

        <div className="input-field">
          <input
            id="image"
            name="image"
            value={form.image}
            onChange={handleChange}
          />
          <label className="active" htmlFor="image">Изображение (URL)</label>
        </div>

        <div className="input-field">
          <textarea
            id="content"
            name="content"
            className="materialize-textarea"
            value={form.content}
            onChange={handleChange}
          ></textarea>
          <label className="active" htmlFor="content">Описание</label>
        </div>

        <div className="input-field">
          <select
            name="category"
            value={form.category}
            onChange={handleChange}
            className="browser-default"
          >
            <option value="">Без категории</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <button className="btn" type="submit">
          Отправить
        </button>
      </form>
    </div>
  );
}

export default AddNews;
