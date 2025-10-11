// Путь: frontend/src/pages/FeedPage.js
// Назначение: Главная лента — карточки с фото и текстовые новости.
// Обновление:
// ✅ fetchNews возвращает массив — адаптировано под новый формат
// ✅ Добавлена универсальная обработка пагинации (hasMore = data.next или data.length > 0)
// ✅ В остальном структура без изменений

import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import InfiniteScroll from "react-infinite-scroll-component";
import { fetchNews } from "../Api";
import SourceLabel from "../components/SourceLabel";
import NewsCard from "../components/NewsCard";
import s from "./FeedPage.module.css";

export default function FeedPage() {
  const [photoNews, setPhotoNews] = useState([]);
  const [textNews, setTextNews] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  // Проверка наличия текста
  function hasSomeText(n) {
    if (!n) return false;
    const tmp = document.createElement("div");
    tmp.innerHTML = n.summary || "";
    const plain = tmp.textContent || tmp.innerText || "";
    return (n.title && n.title.trim() !== "") || plain.trim() !== "";
  }

  // Проверка валидности изображения
  function hasValidImage(n) {
    const img = n.image || n.cover_image || n.preview_image || n.thumbnail;
    if (!img) return false;
    const s = String(img);
    return !s.includes("default_news.svg");
  }

  // Загрузка новостей
  async function loadNews() {
    try {
      const data = await fetchNews(page);

      // ✅ fetchNews теперь возвращает массив, а не объект
      const results = Array.isArray(data)
        ? data
        : Array.isArray(data.results)
        ? data.results
        : [];

      const valid = results.filter(hasSomeText);
      const withPhoto = valid.filter(hasValidImage);
      const withoutPhoto = valid.filter((n) => !hasValidImage(n));

      setPhotoNews((prev) => [...prev, ...withPhoto]);
      setTextNews((prev) => [...prev, ...withoutPhoto]);

      // Если в ответе < 10 элементов — считаем, что новостей больше нет
      setHasMore(results.length > 0);
      setPage((p) => p + 1);
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
    <div className={`${s["feed-page"]} max-w-7xl mx-auto py-6`}>
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
            <div className={s["news-grid"]}>
              {photoNews.map((item, idx) => (
                <NewsCard
                  key={`${item.id ?? item.slug ?? idx}-${idx}`}
                  item={item}
                />
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
                  to={n.seo_url ?? `/news/${n.slug ?? "#"}`}
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
