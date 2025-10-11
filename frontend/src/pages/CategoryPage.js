// Путь: frontend/src/pages/CategoryPage.js
// Назначение: универсальная страница категорий IzotovLife.
// Работает и как список всех категорий (/categories), и как страница одной категории (/politika/).
// Обновления:
//   ✅ Короткие SEO-пути категорий: /<slug>/
//   ✅ /categories показывает сетку карточек категорий
//   ✅ fetchCategoryNews и fetchCategories синхронизированы с backend
//   ✅ Топ-изображение берётся из популярной новости категории (если задано)
//   ✅ Ничего не удалено, только улучшено.

import React, { useEffect, useState } from "react";
import { useParams, useLocation, Link } from "react-router-dom";
import { fetchCategoryNews, fetchCategories } from "../Api";
import NewsCard from "../components/NewsCard";
import Breadcrumbs from "../components/Breadcrumbs";

export default function CategoryPage() {
  const { slug } = useParams(); // например /politika/
  const location = useLocation();
  const isAllCategoriesPage = location.pathname === "/categories";
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [categoryName, setCategoryName] = useState("");
  const [loading, setLoading] = useState(true);

  // -------------------- ЗАГРУЗКА --------------------
  useEffect(() => {
    setLoading(true);

    if (isAllCategoriesPage) {
      // ✅ Страница всех категорий
      fetchCategories()
        .then((data) => {
          const arr = Array.isArray(data)
            ? data
            : data.results || data.items || [];
          setCategories(arr);
        })
        .catch((err) => {
          console.error("Ошибка загрузки категорий:", err);
        })
        .finally(() => setLoading(false));
    } else if (slug) {
      // ✅ Страница конкретной категории
      const loadCategory = async () => {
        try {
          const data = await fetchCategoryNews(slug);
          const arr = Array.isArray(data)
            ? data
            : data.results || data.items || [];
          setItems(arr);
          if (arr.length > 0 && arr[0].category?.name) {
            setCategoryName(arr[0].category.name);
          } else {
            setCategoryName(slug);
          }
        } catch (err) {
          console.error("Ошибка загрузки новостей категории:", err);
          setCategoryName(slug);
        } finally {
          setLoading(false);
        }
      };
      loadCategory();
    }
  }, [slug, isAllCategoriesPage]);

  // -------------------- ОТОБРАЖЕНИЕ --------------------
  if (loading) return <p className="text-white p-4">Загрузка...</p>;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <Breadcrumbs />

      {isAllCategoriesPage ? (
        // ---------- СПИСОК ВСЕХ КАТЕГОРИЙ ----------
        <>
          <h1 className="text-2xl font-bold text-white mb-6">Все категории</h1>

          {categories.length === 0 ? (
            <p className="text-gray-400">Категории не найдены.</p>
          ) : (
            <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {categories.map((cat) => (
                <Link
                  to={`/${cat.slug}/`}
                  key={cat.slug}
                  className="block bg-gray-800 rounded-lg shadow hover:shadow-xl hover:bg-gray-700 transition overflow-hidden"
                >
                  {cat.top_image ? (
                    <div className="relative w-full h-40 overflow-hidden">
                      <img
                        src={cat.top_image}
                        alt={cat.name}
                        className="w-full h-40 object-cover transform hover:scale-105 transition-transform duration-300"
                      />
                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition">
                        <span className="text-white font-semibold text-lg text-center px-2">
                          {cat.name}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="w-full h-40 bg-gray-700 flex items-center justify-center text-gray-300">
                      {cat.name}
                    </div>
                  )}
                </Link>
              ))}
            </div>
          )}
        </>
      ) : (
        // ---------- СТРАНИЦА ОДНОЙ КАТЕГОРИИ ----------
        <>
          <h2 className="text-2xl font-bold text-white mb-4">
  Новостные категории:&nbsp;
  {categoryName && categoryName !== slug ? (
    <span className="text-yellow-400">{categoryName}</span>
  ) : (
    <span className="text-yellow-400" style={{ opacity: 0 }}>{slug}</span>
  )}
</h2>


          {items.length === 0 ? (
            <p className="text-gray-400">Пока нет новостей в этой категории.</p>
          ) : (
            <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {items.map((n) => (
                <NewsCard key={`${n.type}-${n.id}`} item={n} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
