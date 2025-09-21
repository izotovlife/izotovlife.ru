// frontend/src/components/Breadcrumbs.js
// Назначение: Универсальные хлебные крошки для страниц (новости, категории и т.д.)
// Путь: frontend/src/components/Breadcrumbs.js

import React from "react";
import { Link, useLocation } from "react-router-dom";

/**
 * Компонент хлебных крошек
 * Строит цепочку ссылок на основе текущего пути (location.pathname).
 */
export default function Breadcrumbs() {
  const location = useLocation();
  const parts = location.pathname.split("/").filter(Boolean);

  // Генерируем ссылки по частям пути
  const crumbs = parts.map((part, index) => {
    const path = "/" + parts.slice(0, index + 1).join("/");
    const isLast = index === parts.length - 1;

    return (
      <span key={path} className="breadcrumb-item">
        {isLast ? (
          <span className="text-gray-400">{decodeURIComponent(part)}</span>
        ) : (
          <Link to={path} className="text-blue-500 hover:underline">
            {decodeURIComponent(part)}
          </Link>
        )}
      </span>
    );
  });

  return (
    <nav className="text-sm mb-4">
      <Link to="/" className="text-blue-500 hover:underline">
        Главная
      </Link>
      {crumbs.length > 0 && <span className="mx-1">/</span>}
      {crumbs.map((c, i) => (
        <React.Fragment key={i}>
          {c}
          {i < crumbs.length - 1 && <span className="mx-1">/</span>}
        </React.Fragment>
      ))}
    </nav>
  );
}
