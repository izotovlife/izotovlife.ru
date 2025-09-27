// frontend/src/pages/FeedPage.js
// Назначение: Главная лента — 2 колонки карточек с фото + 1 колонка текстовых новостей.
// Что добавлено/исправлено:
//  • hasText теперь «строгий»: вырезает HTML/nbsp и проверяет реальный текст.
//  • Проверка картинки учитывает image/cover_image/preview_image/thumbnail и исключает заглушки.
//  • Правильные ссылки на детали сохраняем: /news/article/:slug или /news/imported/:id.
//  • Вывод источника через <SourceLabel item={...}/> остаётся.
// Путь: frontend/src/pages/FeedPage.js

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
  // textContent уже без тегов; дополнительно убираем nbsp и лишние пробелы
  const text = (el.textContent || el.innerText || "").replace(/\u00A0/g, " ");
  return text.replace(/\s+/g, " ").trim();
}

export default function FeedPage() {
  const [photoNews, setPhotoNews] = useState([]);   // новости с фото
  const [textNews, setTextNews] = useState([]);     // текстовые новости
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // строгая проверка — есть ли у новости ТЕКСТ после очистки HTML
  function hasText(n) {
    const candidates = [
      n.summary,
      n.description,
      n.content,
      n.text,
      n.full_text,
      n.body,
    ];
    for (const c of candidates) {
      const plain = extractPlainText(c);
      if (plain && plain.length > 0) return true; // при желании здесь можно поднять пороги
    }
    return false;
  }

  // валидная ли картинка (не заглушка)
  function hasValidImage(n) {
    const img = n.image || n.cover_image || n.preview_image || n.thumbnail;
    if (!img) return false;
    const s = String(img);
    // отфильтруем статики-заглушки
    if (s.includes("default_news.svg")) return false;
    return true;
  }

  // правильная ссылка на детальную
  function getDetailHref(n) {
    if (n.type === "article" && n.slug) return `/news/article/${n.slug}`;
    if (n.type === "imported" && n.id != null) return `/news/imported/${n.id}`;

    // Если тип не задан — попробуем угадать
    if (n.slug && !/^\d+$/.test(String(n.slug))) return `/news/article/${n.slug}`;
    if (n.slugOrId && n.type) return `/news/${n.type}/${n.slugOrId}`;
    if (n.slugOrId) {
      return /^\d+$/.test(String(n.slugOrId))
        ? `/news/imported/${n.slugOrId}`
        : `/news/article/${n.slugOrId}`;
    }
    if (n.id != null) return `/news/imported/${n.id}`;
    return "#";
  }

  async function loadNews() {
    try {
      const data = await fetchNews(page);
      const results = Array.isArray(data?.results) ? data.results : [];

      // 1) выбрасываем «пустышки» (после очистки HTML)
      const valid = results.filter(hasText);

      // 2) делим на с фото / без фото
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
            endMessage={<p className="text-gray-400 mt-4">Больше новостей нет</p>}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {photoNews.map((n, idx) => (
                <NewsCard key={`${n.id ?? n.slug ?? idx}-${idx}`} item={n} />
              ))}
            </div>
          </InfiniteScroll>
        </div>

        {/* Правая колонка — текстовые */}
        <div>
          <h2 className="text-lg font-bold mb-3">Текстовые новости</h2>
          <ul className="space-y-3">
            {textNews.map((n, idx) => (
              <li key={`text-${n.id ?? n.slug ?? idx}-${idx}`} className="border-b border-gray-700 pb-2">
                <Link to={getDetailHref(n)} className="block hover:underline text-sm font-medium">
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
