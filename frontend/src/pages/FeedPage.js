// Путь: frontend/src/pages/FeedPage.js
// Назначение: Главная лента — 2 колонки карточек с фото + 1 колонка текстовых новостей.
// Исправлено: теперь новости отображаются корректно (все RSS и статьи),
// фильтрация «пустых» новостей ослаблена (учитывает title/summary).

import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import InfiniteScroll from "react-infinite-scroll-component";
import { fetchNews } from "../Api";
import NewsCard from "../components/NewsCard";
import SourceLabel from "../components/SourceLabel";

// --- Утилита: очистка HTML -> обычный текст (убираем теги и NBSP) ---
function extractPlainText(html) {
  if (!html || typeof html !== "string") return "";
  const el = document.createElement("div");
  el.innerHTML = html;
  const text = (el.textContent || el.innerText || "").replace(/\u00A0/g, " ");
  return text.replace(/\s+/g, " ").trim();
}

export default function FeedPage() {
  const [photoNews, setPhotoNews] = useState([]); // новости с фото
  const [textNews, setTextNews] = useState([]); // текстовые новости
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Проверка наличия текста (ослабленная)
  function hasSomeText(n) {
    const plainSummary = extractPlainText(n.summary);
    return (
      (n.title && n.title.trim() !== "") ||
      (plainSummary && plainSummary.length > 0)
    );
  }

  // Проверка валидности изображения
  function hasValidImage(n) {
    const img = n.image || n.cover_image || n.preview_image || n.thumbnail;
    if (!img) return false;
    const s = String(img);
    return !s.includes("default_news.svg");
  }

  // Формирование корректной ссылки на детальную страницу
  function getDetailHref(n) {
    if ((n.type === "article" || n.type === "rss") && n.slug) {
      return `/news/${n.slug}`;
    }
    if (n.slug) return `/news/${n.slug}`;
    return "#";
  }

  // Основная функция загрузки
  async function loadNews() {
    try {
      const data = await fetchNews(page);
      const results = Array.isArray(data?.results) ? data.results : [];

      // ✅ Фильтруем только откровенно пустые записи
      const valid = results.filter(hasSomeText);

      // ✅ Делим на с фото / без фото
      const withPhoto = valid.filter(hasValidImage);
      const withoutPhoto = valid.filter((n) => !hasValidImage(n));

      setPhotoNews((prev) => [...prev, ...withPhoto]);
      setTextNews((prev) => [...prev, ...withoutPhoto]);

      setHasMore(Boolean(data?.next));
      setPage((prev) => prev + 1);
    } catch (err) {
      console.error("Ошибка загрузки новостей:", err);
      setHasMore(false);
    }
  }

  useEffect(() => {
    loadNews();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Левая и центральная колонка — карточки */}
        <div className="lg:col-span-2">
          <InfiniteScroll
            dataLength={photoNews.length}
            next={loadNews}
            hasMore={hasMore}
            loader={<p className="text-gray-400">Загрузка...</p>}
            endMessage={
              <p className="text-gray-400 mt-4">Больше новостей нет</p>
            }
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {photoNews.map((n, idx) => (
                <NewsCard key={`${n.id ?? n.slug ?? idx}-${idx}`} item={n} />
              ))}
            </div>
          </InfiniteScroll>
        </div>

        {/* Правая колонка — текстовые новости */}
        <div>
          <h2 className="text-lg font-bold mb-3">Текстовые новости</h2>
          <ul className="space-y-3">
            {textNews.map((n, idx) => (
              <li
                key={`text-${n.id ?? n.slug ?? idx}-${idx}`}
                className="border-b border-gray-700 pb-2"
              >
                <Link
                  to={getDetailHref(n)}
                  className="block hover:underline text-sm font-medium"
                >
                  {n.title}
                </Link>
                <SourceLabel item={n} className="text-xs text-gray-400" />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
