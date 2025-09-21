// frontend/src/pages/FeedPage.js
// Главная лента: слева новости с фото (по 2 в ряд), справа текстовые.
// Использует хук useNewsFeed с ленивой подгрузкой.
// Заголовки убраны, добавлено визуальное разделение.
// Путь: frontend/src/pages/FeedPage.js

import React from "react";
import useNewsFeed from "../hooks/useNewsFeed";
import NewsCardText from "../components/NewsCardText";
import NewsCardImage from "../components/NewsCardImage";

export default function FeedPage() {
  const { textOnly, withImages, loading, hasMore, loaderRef } = useNewsFeed({});

  // ключ: чтобы React не ругался на дубликаты
  const makeKey = (item, index) => {
    const base =
      (item.type && item.id && `${item.type}-${item.id}`) ||
      (item.slug && `slug-${item.slug}`) ||
      (item.source_url && `url-${item.source_url}`) ||
      "item";
    return `${base}-${index}`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Левая колонка: фото-новости */}
        <section className="lg:col-span-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {withImages.map((n, idx) => (
              <NewsCardImage key={makeKey(n, idx)} item={n} />
            ))}
          </div>

          {loading && (
            <div className="text-sm text-gray-400 mt-3">Загрузка...</div>
          )}
          {!hasMore && !loading && (
            <div className="text-sm text-gray-400 mt-3">
              Больше новостей нет
            </div>
          )}
        </section>

        {/* Правая колонка: текстовые новости, отделены границей */}
        <section className="space-y-3 border-t lg:border-t-0 lg:border-l border-[var(--border)] pt-6 lg:pt-0 lg:pl-6">
          {textOnly.map((n, idx) => (
            <NewsCardText key={makeKey(n, idx)} item={n} />
          ))}

          {!textOnly.length && !loading && (
            <div className="text-sm text-gray-400">Нет текстовых новостей</div>
          )}
        </section>
      </div>

      {/* loaderRef для IntersectionObserver — общий для всей страницы */}
      <div ref={loaderRef} />
    </div>
  );
}
