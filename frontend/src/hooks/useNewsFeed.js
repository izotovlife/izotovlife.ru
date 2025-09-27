// frontend/src/hooks/useNewsFeed.js
// Назначение: бесконечная подгрузка новостей из общей ленты (/feed/).
// Оптимизация: грузим сразу 2 страницы при старте (параллельно),
// убираем дубликаты по type+id/slug/source_url, подставляем дефолтный type = "rss"
// Путь: frontend/src/hooks/useNewsFeed.js

import { useEffect, useState, useRef, useCallback } from "react";
import { fetchFeed } from "../Api";

// Уникализация по type+id/slug/source_url
function uniqById(items) {
  const seen = new Set();
  return items.filter((it) => {
    const key = `${it.type || "rss"}-${it.id || it.slug || it.source_url}`;
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export default function useNewsFeed({ category } = {}) {
  const [textOnly, setTextOnly] = useState([]);     // только без фото
  const [withImages, setWithImages] = useState([]); // только с фото
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const loaderRef = useRef(null);

  // функция загрузки страницы
  const loadNews = useCallback(
    async (p = page) => {
      if (loading || !hasMore) return;
      setLoading(true);

      try {
        const params = { page: p, page_size: 30 };
        if (category) params.category = category;

        const data = await fetchFeed(params);
        const results = (data.results || []).map((n) => ({
          ...n,
          type: n.type || "rss", // ⚡ дефолтное значение
        }));

        const newText = results.filter((n) => !n.image);
        const newImages = results.filter((n) => n.image);

        setTextOnly((prev) => uniqById([...prev, ...newText]));
        setWithImages((prev) => uniqById([...prev, ...newImages]));

        // DRF: next=null → больше страниц нет
        if (!data.next) {
          setHasMore(false);
        }
      } catch (err) {
        console.error("Ошибка загрузки новостей:", err);
      } finally {
        setLoading(false);
      }
    },
    [page, category, hasMore, loading]
  );

  // первая загрузка — сразу 2 страницы (параллельно)
  useEffect(() => {
    (async () => {
      try {
        await Promise.all([loadNews(1), loadNews(2)]);
        setPage(2);
      } catch (err) {
        console.error("Ошибка начальной загрузки:", err);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category]);

  // грузим при изменении page (начиная с 3-й)
  useEffect(() => {
    if (page > 2) loadNews(page);
  }, [page, loadNews]);

  // IntersectionObserver для ленивой подгрузки
  useEffect(() => {
    if (!loaderRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          setPage((p) => p + 1);
        }
      },
      { threshold: 1.0 }
    );

    observer.observe(loaderRef.current);
    return () => observer.disconnect();
  }, [loaderRef, hasMore, loading]);

  return { textOnly, withImages, loading, hasMore, loaderRef };
}
