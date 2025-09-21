// frontend/src/pages/NewsDetailPage.js
// Назначение: Детальная страница новости (Article или RSS).
// Путь: frontend/src/pages/NewsDetailPage.js

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchArticle, fetchImportedNews } from "../Api";
import Breadcrumbs from "../components/Breadcrumbs";

function formatDate(dt) {
  if (!dt) return "";
  try {
    return new Date(dt).toLocaleString("ru-RU");
  } catch {
    return dt;
  }
}

// helper: убираем <img> и "Читать далее" из html
function sanitizeContent(html) {
  if (!html) return "";
  let cleaned = html.replace(/<img[^>]*>/gi, ""); // убрать картинки
  cleaned = cleaned.replace(
    /<a[^>]*>(\s*Читать далее\s*)<\/a>/gi,
    ""
  ); // убрать ссылки "Читать далее"
  return cleaned;
}

export default function NewsDetailPage() {
  const { type, slugOrId } = useParams(); // см. роутинг: /article/:slug или /rss/:id
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setErr("");
      try {
        if (type === "article") {
          const data = await fetchArticle(slugOrId);
          data.type = "article";
          data.image = data.cover_image;
          setItem(data);
        } else if (type === "rss") {
          const data = await fetchImportedNews(slugOrId);
          data.type = "rss";
          setItem(data);
        }
      } catch (e) {
        setErr(e?.message || "Ошибка загрузки");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [type, slugOrId]);

  if (loading) return <div className="p-6">Загрузка…</div>;
  if (err) return <div className="p-6 text-red-500">Ошибка: {err}</div>;
  if (!item) return <div className="p-6">Новость не найдена</div>;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6">
      {/* хлебные крошки */}
      <Breadcrumbs />

      <h1 className="text-3xl font-bold text-white mb-4">{item.title}</h1>

      <div className="text-sm text-gray-400 mb-4">
        {item.source || (item.type === "rss" ? "RSS" : "Автор")}
        {item.published_at ? ` • ${formatDate(item.published_at)}` : ""}
      </div>

      {/* Показываем картинку только один раз */}
      {item.image && (
        <img
          src={item.image}
          alt=""
          className="w-full max-h-[420px] object-cover rounded-xl mb-4"
        />
      )}

      {/* Контент без картинок и лишних ссылок */}
      <div
        className="prose prose-invert max-w-none"
        dangerouslySetInnerHTML={{
          __html: sanitizeContent(item.content || item.summary || ""),
        }}
      />

      {/* Ссылка на источник */}
      {item.type === "rss" && item.source_url ? (
        <a
          href={item.source_url}
          target="_blank"
          rel="noreferrer"
          className="text-blue-400 hover:underline mt-6 block text-lg"
        >
          Читать в источнике →
        </a>
      ) : null}
    </div>
  );
}
