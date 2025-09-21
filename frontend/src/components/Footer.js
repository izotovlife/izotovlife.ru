// frontend/src/components/Footer.js

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchPages } from "../Api";

export default function Footer() {
  const [pages, setPages] = useState([]);

  useEffect(() => {
    fetchPages().then(setPages).catch(console.error);
  }, []);

  const mandatoryPages = [
    { slug: "politika-konfidencialnosti", title: "Политика конфиденциальности" },
    { slug: "pravila-ispolzovaniya", title: "Правила использования" },
    { slug: "o-kompanii", title: "О компании" },
    { slug: "redakcionnaya-politika", title: "Редакционная политика" },
    { slug: "reklama", title: "Реклама" },
    { slug: "kontakty", title: "Контакты" }
  ];

  // Защита: если API вдруг вернёт не массив
  const safePages = Array.isArray(pages) ? pages : [];
  const extraPages = safePages.filter(
    (p) => !mandatoryPages.find((m) => m.slug === p.slug)
  );

  return (
    <footer className="bg-[var(--bg-card)] border-t border-[var(--border)] py-6 mt-8">
      <div className="max-w-7xl mx-auto px-4 text-sm text-gray-400">
        <div className="flex flex-wrap gap-4">
          {mandatoryPages.map((p) => (
            <Link key={p.slug} to={`/page/${p.slug}`} className="hover:text-white transition">
              {p.title}
            </Link>
          ))}
          {extraPages.map((p) => (
            <Link key={p.id} to={`/page/${p.slug}`} className="hover:text-white transition">
              {p.title}
            </Link>
          ))}
        </div>
        <div className="mt-4 text-xs text-gray-500">
          © {new Date().getFullYear()} IzotovLife.ru — Все права защищены
        </div>
      </div>
    </footer>
  );
}
