// frontend/src/components/Header.js
// Шапка сайта с логотипом и выбором категорий
import React, { useEffect, useState } from "react";

function Header() {
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetch("/api/categories/")
      .then(res => res.json())
      .then(data => setCategories(data));
  }, []);

  return (
    <header className="bg-[var(--color-primary)] text-white p-4 flex items-center justify-between">
      <h1 className="font-bold text-xl">Новости</h1>
      <nav>
        <ul className="flex gap-4">
          {categories.map(cat => (
            <li key={cat.id}>
              <a href={`/category/${cat.slug}`} className="hover:underline">
                {cat.name}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}

export default Header;
