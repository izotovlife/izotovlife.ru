// Путь: frontend/src/components/NewsCard.js
// Назначение: Карточка новости для ленты (в стиле Дзена, SEO-ready).
// Обновление:
//   ✅ Источник теперь берётся корректно из source_name, source_fk, link (без RSS).
//   ✅ Повышена устойчивость к невалидным данным.
//   ✅ Полностью совместимо с SourceBadge и темами.
//   ✅ Добавлено: плавное появление карточек при скролле и мягкий градиент под текстом.
//   ✅ [SEO] Основной путь теперь /<category>/<slug>, с fallback на старые /news/... схемы.

import React, { useMemo, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import s from "./NewsCard.module.css";
import SourceBadge from "./SourceBadge";
import placeholder from "../assets/default_news.svg";

// -------------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ --------------------

function hostName(url) {
  try {
    const u = new URL(url);
    let h = u.hostname || "";
    h = h.replace(/^www\./i, "").replace(/^m\./i, "").replace(/^amp\./i, "");
    const parts = h.split(".");
    if (parts.length > 2) return parts.slice(-2).join(".");
    return h || null;
  } catch {
    return null;
  }
}

// Унифицированное получение источника
function resolveSource(item) {
  const sourceObj =
    item.source ||
    item.news_source ||
    item.source_fk ||
    item.publisher_obj ||
    null;

  const sourceUrl =
    sourceObj?.site_url ||
    sourceObj?.url ||
    sourceObj?.link ||
    item.source_url ||
    item.site_url ||
    item.link_source ||
    item.original_link ||
    item.original_url ||
    item.link ||
    item.url ||
    null;

  const sourceNameRaw =
    item.source_name ||
    item.source_title ||
    item.publisher ||
    item.sourceDomain ||
    sourceObj?.name ||
    sourceObj?.title ||
    null;

  let sourceName = null;
  if (sourceNameRaw && sourceNameRaw.toLowerCase() !== "rss") {
    sourceName = sourceNameRaw;
  } else {
    sourceName = hostName(sourceUrl) || "Источник";
  }

  return {
    name: sourceName,
    site_url: sourceUrl,
    logo:
      item.source_logo ||
      sourceObj?.logo ||
      sourceObj?.image ||
      sourceObj?.icon ||
      null,
  };
}

// -------------------- ОСНОВНОЙ ХУК --------------------

function useNormalized(item) {
  return useMemo(() => {
    const id = item.id ?? item.pk ?? item._id ?? null;
    const title = item.title || item.headline || item.name || "Без названия";

    const slug =
      item.slug ||
      item.seo_slug ||
      item.url_slug ||
      item.seourl ||
      item.slugified ||
      null;

    const categorySlug =
      item.category_slug ||
      item.category?.slug ||
      item.category?.seo_slug ||
      item.categories?.[0]?.slug ||
      null;

    // ✅ SEO-ссылка /<category>/<slug> с fallback’ами
    let detailTo = "#";
    if (item.seo_url) {
      // если backend уже прислал готовый seo_url
      detailTo = item.seo_url;
    } else if (categorySlug && slug) {
      // основной путь
      detailTo = `/${categorySlug}/${slug}`;
    } else if (slug) {
      // старый fallback /news/<slug>
      detailTo = `/news/${slug}`;
    } else if (id) {
      // совсем fallback
      detailTo = `/news/${id}`;
    }

    const cover =
      item.cover_image ||
      item.image_url ||
      item.image ||
      item.thumbnail ||
      null;

    const source = resolveSource(item);

    const date =
      item.published_at || item.pub_date || item.created_at || item.date || null;

    const categoryName = item.category_name || item.category?.name || null;

    return { id, title, detailTo, cover, source, date, categoryName };
  }, [item]);
}

// -------------------- КОМПОНЕНТ --------------------

export default function NewsCard({ item, badgeAlign = "right" }) {
  const { title, detailTo, cover, source, date, categoryName } =
    useNormalized(item);

  const dateStr = useMemo(() => {
    if (!date) return null;
    try {
      const d = new Date(date);
      if (Number.isNaN(d.getTime())) return null;
      return d.toLocaleDateString("ru-RU", {
        year: "numeric",
        month: "short",
        day: "2-digit",
      });
    } catch {
      return null;
    }
  }, [date]);

  const hasCover = Boolean(cover);

  // -------------------- ДОБАВЛЕНО --------------------
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        el.classList.add(s.visible);
        observer.disconnect();
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  // ---------------------------------------------------

  return (
    <article ref={ref} className={`${s.card} news-card`}>
      <Link to={detailTo} className={s.mediaWrap} aria-label={title}>
        <img
          className={s.media}
          src={hasCover ? cover : placeholder}
          alt={title}
          loading="lazy"
          onError={(e) => {
            e.currentTarget.src = placeholder;
          }}
        />
        {hasCover ? (
          <SourceBadge
            source={source}
            href={source.site_url || undefined}
            align={badgeAlign}
            insideLink
          />
        ) : null}
      </Link>

      <div className={s.body}>
        <h3 className={s.title}>
          <Link to={detailTo}>{title}</Link>
        </h3>

        {!hasCover ? (
          <div className={s.sourceLine}>
            <span className={s.sourceDot} />
            <span className={s.sourceText}>{source.name}</span>
          </div>
        ) : null}

        <div className={s.meta}>
          {categoryName ? <span className={s.cat}>{categoryName}</span> : null}
          {dateStr ? <time className={s.date}>{dateStr}</time> : null}
        </div>
      </div>
    </article>
  );
}
