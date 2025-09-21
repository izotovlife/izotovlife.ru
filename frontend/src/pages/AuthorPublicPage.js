// frontend/src/pages/AuthorPublicPage.js
// Назначение: Публичная страница автора с его статьями.
// Путь: frontend/src/pages/AuthorPublicPage.js

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../Api";

export default function AuthorPublicPage() {
  const { id } = useParams();
  const [author, setAuthor] = useState(null);
  const [articles, setArticles] = useState([]);

  useEffect(() => {
    async function load() {
      const { data } = await api.get(`/api/accounts/${id}/`);
      setAuthor(data);
      const { data: arts } = await api.get(
        `/api/news/author/articles/?author=${id}&status=PUBLISHED`
      );
      setArticles(arts);
    }
    load();
  }, [id]);

  if (!author) return <div>Загрузка…</div>;

  return (
    <div>
      <h1>{author.username}</h1>
      {author.photo && (
        <img
          src={author.photo}
          alt={author.username}
          style={{ width: "120px", borderRadius: "50%" }}
        />
      )}
      <p>{author.bio}</p>

      <h2>Статьи</h2>
      {articles.map((a) => (
        <div key={a.id} className="card">
          <h3>{a.title}</h3>
          {a.cover_image && <img src={a.cover_image} alt="" width="200" />}
          <div dangerouslySetInnerHTML={{ __html: a.content.slice(0, 200) }} />
        </div>
      ))}
    </div>
  );
}
