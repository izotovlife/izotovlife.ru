// frontend/src/pages/CategoryPage.js
// Назначение: Страница списка новостей по категории
// Путь: frontend/src/pages/CategoryPage.js

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchCategoryNews } from "../Api";
import NewsCardText from "../components/NewsCardText";
import Breadcrumbs from "../components/Breadcrumbs";

export default function CategoryPage() {
  const { slug } = useParams();
  const [items, setItems] = useState([]);

  useEffect(() => {
    fetchCategoryNews(slug).then(setItems).catch(console.error);
  }, [slug]);

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* хлебные крошки */}
      <Breadcrumbs />

      <h2 className="text-2xl font-bold text-white mb-4">
        Новости категории: {slug}
      </h2>

      <div className="grid gap-4">
        {items.map((n) => (
          <NewsCardText key={n.id} item={n} />
        ))}
      </div>
    </div>
  );
}
