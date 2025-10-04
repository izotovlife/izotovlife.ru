// Путь: frontend/src/pages/CategoryPage.js
// Назначение: универсальная страница категорий.
// Если есть slug → показываем новости в категории.
// Если slug нет → показываем все категории с обложкой (топ-новость).

import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchCategoryNews, fetchCategories } from "../Api";
import NewsCard from "../components/NewsCard";
import Breadcrumbs from "../components/Breadcrumbs";

export default function CategoryPage() {
  const { slug } = useParams();
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (slug) {
      // Новости конкретной категории
      fetchCategoryNews(slug)
        .then((data) => {
          const arr = Array.isArray(data) ? data : data.results || data.items || [];
          setItems(arr);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Ошибка загрузки новостей категории:", err);
          setLoading(false);
        });
    } else {
      // Все категории
      fetchCategories()
        .then((data) => {
          const arr = Array.isArray(data) ? data : data.results || data.items || [];
          setCategories(arr);
          setLoading(false);
        })
        .catch((err) => {
          console.error("Ошибка загрузки категорий:", err);
          setLoading(false);
        });
    }
  }, [slug]);

  if (loading) return <p className="text-white p-4">Загрузка...</p>;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <Breadcrumbs />

      {slug ? (
        <>
          <h2 className="text-2xl font-bold text-white mb-4">
            Новости категории: {slug}
          </h2>
          <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {items.map((n) => (
              <NewsCard key={`${n.type}-${n.id}`} item={n} />
            ))}
          </div>
        </>
      ) : (
        <>
          <h1 className="text-2xl font-bold text-white mb-6">Все категории</h1>
          <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {categories.map((cat) => (
              <Link
                to={`/category/${cat.slug}`}
                key={cat.slug}
                className="block bg-gray-800 rounded-lg shadow hover:bg-gray-700 transition overflow-hidden"
              >
                {/* Картинка категории (топ-новость) */}
                {cat.top_image ? (
                  <img
                    src={cat.top_image}
                    alt={cat.name}
                    className="w-full h-40 object-cover"
                  />
                ) : (
                  <div className="w-full h-40 bg-gray-600 flex items-center justify-center text-gray-300">
                    Нет изображения
                  </div>
                )}

                {/* Название категории */}
                <div className="p-4 text-center text-white font-medium">
                  {cat.name}
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
