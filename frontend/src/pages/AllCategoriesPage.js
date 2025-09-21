// frontend/src/pages/AllCategoriesPage.js
// Назначение: Список всех категорий (для кнопки "Все категории").
// Путь: frontend/src/pages/AllCategoriesPage.js

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchCategories } from "../Api";

export default function AllCategoriesPage() {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchCategories().then(setCategories).catch(console.error);
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Все категории</h1>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {categories.map((cat) => (
          <Link
            key={cat.id}
            to={`/category/${cat.slug}`}
            className="block p-4 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition"
          >
            {cat.name}
          </Link>
        ))}
      </div>
    </div>
  );
}
