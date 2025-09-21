// frontend/src/pages/AuthorDashboard.js
// Назначение: Личный кабинет автора — вкладки по статусам, редактор статей с загрузкой изображений.
// Путь: frontend/src/pages/AuthorDashboard.js

import React, { useState, useEffect } from "react";
import {
  fetchMyByStatus,
  createArticle,
  submitArticle,
} from "../Api";

import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";

// УСТАНОВИ эти пакеты: npm i react-quill quill-image-uploader
import Quill from "quill";
import ImageUploader from "quill-image-uploader";
Quill.register("modules/imageUploader", ImageUploader);

export default function AuthorDashboard() {
  const [tab, setTab] = useState("DRAFT");
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);

  // поля новой статьи
  const [title, setTitle] = useState("");
  const [coverImage, setCoverImage] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => {
    setLoading(true);
    fetchMyByStatus(tab)
      .then(setArticles)
      .finally(() => setLoading(false));
  }, [tab]);

  async function handleCreate() {
    if (!title.trim() || !content.trim()) {
      alert("Заполните заголовок и текст");
      return;
    }
    const article = await createArticle({
      title,
      content,
      cover_image: coverImage,
    });
    alert("Черновик создан!");
    setTitle("");
    setContent("");
    setCoverImage("");
    setTab("DRAFT");
    setArticles((prev) => [article, ...prev]);
  }

  async function handleSubmit(id) {
    await submitArticle(id);
    alert("Отправлено на модерацию");
    setArticles((prev) => prev.filter((x) => x.id !== id));
  }

  const modules = {
    toolbar: [
      [{ header: [1, 2, 3, false] }],
      ["bold", "italic", "underline", "strike"],
      [{ list: "ordered" }, { list: "bullet" }],
      ["link", "image"],
      ["clean"],
    ],
    imageUploader: {
      upload: async (file) => {
        const formData = new FormData();
        formData.append("image", file);
        const resp = await fetch("http://localhost:8000/api/news/upload-image/", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access") || ""}`,
          },
          body: formData,
        });
        const data = await resp.json();
        if (!resp.ok) {
          throw new Error(data?.error || "Ошибка загрузки изображения");
        }
        return data.url; // Quill вставит <img src="...">
      },
    },
  };

  return (
    <div className="author-dashboard">
      <h1>Кабинет автора</h1>

      {/* Вкладки */}
      <div className="tabs">
        {["DRAFT", "PENDING", "PUBLISHED", "NEEDS_REVISION"].map((status) => (
          <button
            key={status}
            className={tab === status ? "active" : ""}
            onClick={() => setTab(status)}
          >
            {status === "DRAFT" && "Черновики"}
            {status === "PENDING" && "На модерации"}
            {status === "PUBLISHED" && "Опубликованные"}
            {status === "NEEDS_REVISION" && "На доработке"}
          </button>
        ))}
      </div>

      {/* Список статей */}
      {loading ? (
        <div>Загрузка…</div>
      ) : (
        <div className="articles-list">
          {articles.length === 0 && <p>Нет статей</p>}
          {articles.map((a) => (
            <div key={a.id} className="card">
              <h3>{a.title}</h3>
              {a.cover_image && (
                <img
                  src={a.cover_image}
                  alt=""
                  style={{ maxWidth: "200px", marginTop: "8px" }}
                />
              )}
              <div
                style={{ marginTop: 8 }}
                dangerouslySetInnerHTML={{ __html: a.content }}
              />
              {tab === "DRAFT" && (
                <button onClick={() => handleSubmit(a.id)} style={{ marginTop: 8 }}>
                  Отправить на модерацию
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Редактор новой статьи */}
      <div className="editor-section card">
        <h2>Новая статья</h2>
        <input
          type="text"
          placeholder="Заголовок"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          style={{ width: "100%", marginBottom: "8px" }}
        />
        <input
          type="text"
          placeholder="Ссылка на обложку"
          value={coverImage}
          onChange={(e) => setCoverImage(e.target.value)}
          style={{ width: "100%", marginBottom: "8px" }}
        />
        <ReactQuill
          value={content}
          onChange={setContent}
          modules={modules}
          theme="snow"
        />
        <button className="button primary" onClick={handleCreate} style={{ marginTop: 10 }}>
          Сохранить черновик
        </button>
      </div>

      <style>{`
        .tabs {
          display: flex;
          gap: 8px;
          margin: 12px 0;
        }
        .tabs button {
          padding: 6px 12px;
          border: 1px solid #ddd;
          background: #f9f9f9;
          cursor: pointer;
        }
        .tabs button.active {
          background: #0077ff;
          color: white;
        }
        .card {
          border: 1px solid #ddd;
          border-radius: 6px;
          padding: 12px;
          margin: 12px 0;
          background: white;
        }
        .editor-section {
          margin-top: 20px;
        }
      `}</style>
    </div>
  );
}
