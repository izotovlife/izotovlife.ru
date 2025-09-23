// frontend/src/pages/AuthorDashboard.js
// Назначение: Кабинет автора. Управление статьями (создание, список, статусы).
// Путь: frontend/src/pages/AuthorDashboard.js

import React, { useEffect, useState } from "react";
import {
  fetchMyArticles,
  createArticle,
  submitArticle,
} from "../Api";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";

export default function AuthorDashboard() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);

  // поля формы
  const [title, setTitle] = useState("");
  const [content, setContent] = useState(""); // ⚡ здесь будет HTML
  const [categories, setCategories] = useState("");
  const [image, setImage] = useState("");

  const loadArticles = async () => {
    try {
      setLoading(true);
      const data = await fetchMyArticles();
      setArticles(data);
    } catch (err) {
      setError("Ошибка загрузки статей");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadArticles();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        title,
        content, // уже HTML
        categories: categories.split(",").map((c) => c.trim()),
        image,
      };
      const newArticle = await createArticle(payload);
      setArticles((prev) => [newArticle, ...prev]);
      setShowForm(false);
      setTitle("");
      setContent("");
      setCategories("");
      setImage("");
    } catch (err) {
      console.error("Ошибка при создании:", err);
      setError("Не удалось создать статью");
    }
  };

  const handleSubmitArticle = async (id) => {
    try {
      const res = await submitArticle(id);
      setArticles((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: res.status } : a))
      );
    } catch (err) {
      console.error("Ошибка при отправке:", err);
      setError("Не удалось отправить статью на модерацию");
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-6 text-white">
      <h1 className="text-2xl font-bold mb-4">Кабинет автора</h1>

      {error && <div className="text-red-400 mb-4">{error}</div>}

      <button
        onClick={() => setShowForm(!showForm)}
        className="mb-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
      >
        {showForm ? "Отмена" : "Создать статью"}
      </button>

      {showForm && (
        <form onSubmit={handleCreate} className="space-y-3 mb-6">
          <input
            type="text"
            placeholder="Заголовок"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 rounded bg-[var(--bg-card)] border border-gray-600"
            required
          />

          {/* 🔥 WYSIWYG редактор */}
          <ReactQuill
            theme="snow"
            value={content}
            onChange={setContent}
            className="bg-white text-black rounded"
            placeholder="Введите текст статьи..."
            modules={{
              toolbar: [
                [{ header: [1, 2, 3, false] }],
                ["bold", "italic", "underline", "strike"],
                [{ list: "ordered" }, { list: "bullet" }],
                ["link", "image"],
                ["clean"],
              ],
            }}
          />

          <input
            type="text"
            placeholder="Категории (через запятую)"
            value={categories}
            onChange={(e) => setCategories(e.target.value)}
            className="w-full p-2 rounded bg-[var(--bg-card)] border border-gray-600"
          />

          <input
            type="text"
            placeholder="Ссылка на картинку (опционально)"
            value={image}
            onChange={(e) => setImage(e.target.value)}
            className="w-full p-2 rounded bg-[var(--bg-card)] border border-gray-600"
          />

          <button
            type="submit"
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded"
          >
            Сохранить
          </button>
        </form>
      )}

      {loading ? (
        <div>Загрузка...</div>
      ) : articles.length === 0 ? (
        <div>У вас пока нет статей.</div>
      ) : (
        <ul className="space-y-3">
          {articles.map((a) => (
            <li
              key={a.id}
              className="p-3 border border-gray-700 rounded bg-[var(--bg-card)]"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-bold">{a.title}</h3>
                  <p className="text-sm text-gray-400">
                    Статус: {a.status || "DRAFT"}
                  </p>
                </div>
                {a.status === "DRAFT" && (
                  <button
                    onClick={() => handleSubmitArticle(a.id)}
                    className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 rounded"
                  >
                    Отправить на модерацию
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
