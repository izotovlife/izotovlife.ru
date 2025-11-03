/* Путь: frontend/src/pages/CategoriesPage.js
   Назначение: Страница-список всех категорий. Ссылки ведут на короткие пути "/{slug}/".
   Особенности:
   - Загружает список категорий + батч-обложки (быстро) через fetchCategoryCovers().
   - Не трогает CategoryPage.js — та страница остаётся для одной категории (/:slug/).
   - Полностью совместимо с импортом в App.js: import CategoriesPage from "./pages/CategoriesPage";
*/

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import s from "./CategoriesPage.module.css";

import {
  fetchCategories,
  fetchCategoryCovers,   // батч обложек /api/categories/covers/
  buildThumbnailUrl,     // ресайзер (безопасно обрабатывает только http/https)
} from "../Api";

import SmartMedia from "../components/SmartMedia";
import SmartTitle from "../components/SmartTitle";

export default function CategoriesPage() {
  const [cats, setCats] = useState([]);
  const [covers, setCovers] = useState({});
  const [loading, setLoading] = useState(true);
  const [loadingCovers, setLoadingCovers] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    document.title = "Категории — IzotovLife";
  }, []);

  // 1) Загружаем список категорий
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");

    fetchCategories()
      .then((res) => {
        const data = res?.data || res;
        const list = Array.isArray(data) ? data : data?.results || [];
        if (!cancelled) setCats(list);
      })
      .catch(() => !cancelled && setError("Не удалось загрузить категории"))
      .finally(() => !cancelled && setLoading(false));

    return () => { cancelled = true; };
  }, []);

  // 2) Батч-обложки для всех категорий (быстро)
  useEffect(() => {
    let cancelled = false;
    if (!cats.length) {
      setCovers({});
      setLoadingCovers(false);
      return;
    }
    setLoadingCovers(true);
    const slugs = cats.map((c) => c.slug || c.seo_slug || c.url_slug).filter(Boolean);

    fetchCategoryCovers(slugs)
      .then((res) => {
        // ожидаем словарь вида { "<slug>": "https://..." }
        const mapping = res?.data || {};
        if (!cancelled) setCovers(mapping || {});
      })
      .catch(() => !cancelled && setCovers({}))
      .finally(() => !cancelled && setLoadingCovers(false));

    return () => { cancelled = true; };
  }, [cats]);

  const items = useMemo(() => {
    return cats.map((c) => {
      const slug = c.slug || c.seo_slug || c.url_slug || "";
      const name = c.name || c.title || slug;
      const cover =
        covers[slug] ||
        c.cover ||
        c.image ||
        c.thumb ||
        null;

      // прогоняем через ресайзер ТОЛЬКО http/https
      const safeCover = cover ? buildThumbnailUrl(cover, { w: 1200, h: 630, fit: "cover" }) : null;

      return { slug, name, cover: safeCover, count: c.count || c.articles_count || null };
    });
  }, [cats, covers]);

  if (loading) {
    return (
      <div className={s.page}>
        <h1 className={s.title}><SmartTitle>Категории</SmartTitle></h1>
        <div className={s.grid}>
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className={`${s.card} ${s.skeleton}`} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={s.page}>
        <h1 className={s.title}><SmartTitle>Категории</SmartTitle></h1>
        <p className={s.error}>{error}</p>
      </div>
    );
  }

  return (
    <div className={s.page}>
      <h1 className={s.title}><SmartTitle>Категории</SmartTitle></h1>

      <div className={s.grid}>
        {items.map((it) => (
          <article key={it.slug} className={s.card}>
            {/* Короткий путь верхнего уровня */}
            <Link to={`/${it.slug}/`} className={s.cardLink} aria-label={`Категория: ${it.name}`}>
              <div className={s.cardMedia}>
                {it.cover ? (
                  <SmartMedia src={it.cover} alt={it.name} />
                ) : (
                  <div className={s.placeholder} />
                )}
                <div className={s.overlay} />
                <div className={s.caption}>
                  <span className={s.name}>{it.name}</span>
                  {typeof it.count === "number" && (
                    <span className={s.count}>{it.count}</span>
                  )}
                </div>
              </div>
            </Link>
          </article>
        ))}
      </div>

      {/* Покажем мягко состояние подзагрузки обложек, чтобы не дёргать сетку */}
      {loadingCovers && <div className={s.note}>Загружаем обложки…</div>}
    </div>
  );
}
