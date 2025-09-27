// frontend/src/pages/NewsDetailPage.js
// Назначение: Детальная страница новости (Article или импортированная RSS) + «Похожие» + «Читать по теме».
// Обновления:
//   • Убран дубль картинки: если первый <img> в summary совпадает с обложкой — вырезаем его из HTML тела.
//   • Сетка: добавлен левый буфер (как сайдбар) — контент визуально центрируется.
//   • Остальной функционал сохранён (санитайзер, «Подробнее», счётчик просмотров и т.д.).
// Путь: frontend/src/pages/NewsDetailPage.js

import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import DOMPurify from "dompurify";
import s from "./NewsDetailPage.module.css";
import { fetchArticle, fetchImportedNews, fetchCategoryNews } from "../Api";

const API_URL = "http://127.0.0.1:8000";

// ---------------- Утилиты ----------------

function getHostname(url) {
  try {
    const u = new URL(url);
    return u.hostname.replace(/^www\./, "");
  } catch {
    return "";
  }
}

function stripHtml(text) {
  if (!text) return "";
  const tmp = document.createElement("div");
  tmp.innerHTML = text;
  const plain = tmp.textContent || tmp.innerText || "";
  return plain.replace(/\s+/g, " ").trim();
}

function absolutizeUrl(url, base = API_URL) {
  try {
    return new URL(url, base).href;
  } catch {
    return url || "";
  }
}

function absolutizeHtml(html, base = API_URL) {
  if (!html) return "";
  return html.replace(
    /(src|href)\s*=\s*"(\/[^"]*)"/gi,
    (_m, attr, path) => `${attr}="${absolutizeUrl(path, base)}"`
  );
}

/** Вырезает первый <img>, если его src совпадает с coverUrl */
function stripLeadingDuplicateImg(html, coverUrl) {
  if (!html) return "";
  if (!coverUrl) return html;
  const absCover = absolutizeUrl(coverUrl);

  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const img = doc.body.querySelector("img");
    if (img) {
      const src = absolutizeUrl(img.getAttribute("src") || "");
      if (src === absCover) {
        img.remove();
      }
    }
    return doc.body.innerHTML;
  } catch {
    // Фолбэк: удалим самый первый <img ...>
    return html.replace(/<img\b[^>]*>/i, "");
  }
}

function sanitizeHtml(html) {
  const clean = DOMPurify.sanitize(html || "", {
    ALLOWED_TAGS: [
      "p",
      "br",
      "strong",
      "em",
      "ul",
      "ol",
      "li",
      "a",
      "img",
      "blockquote",
      "h3",
      "h4",
      "h5",
      "h6",
      "span",
      "div",
    ],
    ALLOWED_ATTR: ["href", "src", "alt", "title", "target", "rel", "class", "style"],
    ADD_ATTR: ["align"],
    FORBID_TAGS: ["script", "iframe", "object", "embed", "style"],
    RETURN_DOM: false,
  });
  return clean.replace(
    /<a\s+([^>]*href="https?:\/\/[^"]+"[^>]*)>/gi,
    (_m, attrs) => `<a ${attrs} target="_blank" rel="noreferrer noopener">`
  );
}

function buildInternalHref(n) {
  const isImported = !!n?.link && !n?.content;
  if (isImported && (n.id || n.pk)) {
    const id = n.id || n.pk;
    return `/news/i/${id}`;
  }
  if (!isImported && (n.slug || n.id)) {
    const slugOrId = n.slug || n.id;
    return `/news/a/${slugOrId}`;
  }
  return null;
}

function pickBodyHtml(n) {
  if (!n) return "";
  if (n.link) {
    return n.summary || n.description || n.text || "";
  }
  return n.content || n.body || n.text || n.summary || "";
}

function sourceDisplay(n) {
  const name = n?.source?.name || n?.source_name || "";
  if (name) return name;
  const host = getHostname(n?.link || "");
  return host || "Источник";
}

// --------------- Компонент ---------------

export default function NewsDetailPage() {
  const { type, slugOrId } = useParams();

  const [news, setNews] = useState(null);
  const [related, setRelated] = useState([]);
  const [views, setViews] = useState(null);
  const [loading, setLoading] = useState(true);

  // Загрузка основной новости
  useEffect(() => {
    let cancel = false;

    async function load() {
      try {
        setLoading(true);
        let item = null;

        if (type === "i" || type === "imported" || type === "rss") {
          item = await fetchImportedNews(slugOrId);
        } else if (type === "a" || type === "article") {
          item = await fetchArticle(slugOrId);
        } else {
          try {
            item = await fetchArticle(slugOrId);
          } catch {
            item = await fetchImportedNews(slugOrId);
          }
        }

        if (cancel) return;

        setNews(item || null);

        const catSlug =
          item?.category?.slug ||
          item?.category_slug ||
          (item?.category && typeof item.category === "string" ? item.category : null);

        if (catSlug) {
          const rel = (await fetchCategoryNews(catSlug)) || [];
          const currentKey = (item?.slug || "") + "::" + (item?.id || item?.pk || "");
          const filtered = rel.filter((n) => {
            const key = (n?.slug || "") + "::" + (n?.id || n?.pk || "");
            return key !== currentKey;
          });
          setRelated(filtered.slice(0, 12));
        } else {
          setRelated([]);
        }
      } catch (e) {
        console.error(e);
        setNews(null);
        setRelated([]);
      } finally {
        if (!cancel) setLoading(false);
      }
    }

    load();
    return () => {
      cancel = true;
    };
  }, [type, slugOrId]);

  // Обложка
  const coverUrl = useMemo(() => {
    const candidates = [
      news?.cover_image,
      news?.image,
      news?.image_url,
      news?.thumbnail,
    ].filter(Boolean);
    return candidates.length ? candidates[0] : null;
  }, [news]);

  // Готовим тело к выводу: сначала приводим пути к абсолютным, потом убираем дубликат img, затем санитизируем
  const { bodyHtml, bodyText, isEmpty } = useMemo(() => {
    const raw = pickBodyHtml(news);
    const withAbs = absolutizeHtml(raw, API_URL);
    const noDupImg = stripLeadingDuplicateImg(withAbs, coverUrl);
    const sanitized = sanitizeHtml(noDupImg);
    const plain = stripHtml(sanitized);
    const hasImage = /<img\s/i.test(sanitized);
    const reallyEmpty = !hasImage && plain.length < 10;
    return { bodyHtml: sanitized, bodyText: plain, isEmpty: reallyEmpty };
  }, [news, coverUrl]);

  // Инкремент просмотров (если у тебя уже есть блок метрик из прошлой версии — код оставлен)
  useEffect(() => {
    if (!news) return;

    const isImported = !!news?.link && !news?.content;
    const payload =
      isImported
        ? { type: "i", id: news.id || news.pk }
        : { type: "a", slug: news.slug || String(news.id || news.pk) };

    fetch(`${API_URL}/api/metrics/hit/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      credentials: "include",
    })
      .then((r) => r.json())
      .then((data) => {
        if (typeof data?.views === "number") setViews(data.views);
      })
      .catch((e) => console.warn("metrics/hit error", e));
  }, [news]);

  const externalHref = news?.link || null;

  const topicItems = useMemo(() => related.slice(0, 3), [related]);
  const sidebarItems = useMemo(() => related.slice(3), [related]);

  if (loading) {
    return (
      <div className={s.pageWrap}>
        <div className={s.leftPad} aria-hidden="true" />
        <div className={s.main}>Загрузка…</div>
        <aside className={s.sidebar} />
      </div>
    );
  }

  if (!news) {
    return (
      <div className={s.pageWrap}>
        <div className={s.leftPad} aria-hidden="true" />
        <div className={s.main}>Новость не найдена.</div>
        <aside className={s.sidebar} />
      </div>
    );
    }

  return (
    <div className={s.pageWrap}>
      {/* Левый буфер — просто пустой столбец шириной как сайдбар */}
      <div className={s.leftPad} aria-hidden="true" />

      {/* Центральная колонка — основная новость */}
      <article className={s.main}>
        <h1 className={s.title}>{news.title || "Без названия"}</h1>

        <div className={s.meta}>
          Источник: <span style={{ opacity: 0.9 }}>{sourceDisplay(news)}</span>
          {news.published_at ? (
            <span style={{ marginLeft: 12 }}>
              • {new Date(news.published_at).toLocaleString()}
            </span>
          ) : null}
          {typeof views === "number" ? (
            <span style={{ marginLeft: 12 }}>
              • {views} просмотров
            </span>
          ) : null}
        </div>

        {coverUrl ? (
          <img
            src={coverUrl}
            alt=""
            className={s.cover}
            onError={(e) => {
              e.currentTarget.src = `${API_URL}/static/img/default_news.svg`;
            }}
          />
        ) : null}

        {/* Тело */}
        {!isEmpty ? (
          <>
            <div
              className={s.body}
              dangerouslySetInnerHTML={{ __html: bodyHtml }}
            />
            <div className={s.srOnly}>{bodyText}</div>
          </>
        ) : (
          <div className={s.empty}>Краткое описание недоступно.</div>
        )}

        {/* Ссылка на оригинал */}
        {externalHref ? (
          <div className={s.external}>
            <a
              href={externalHref}
              target="_blank"
              rel="noreferrer noopener"
              className={s.externalLink}
            >
              Подробнее в источнике →
            </a>
          </div>
        ) : null}

        {/* Читать по теме */}
        {topicItems.length > 0 && (
          <>
            <h3 className={s.sectionH} style={{ marginTop: 16 }}>Читать по теме</h3>
            <div className={s.topicGrid}>
              {topicItems.map((n) => {
                const inner = buildInternalHref(n);
                const href = inner || n.link || "#";
                const isInternal = !!inner;
                const thumb =
                  n.thumbnail ||
                  n.cover_image ||
                  n.image ||
                  n.image_url ||
                  `${API_URL}/static/img/default_news.svg`;

                const card = (
                  <div className={s.topicCard}>
                    <img
                      src={thumb}
                      alt=""
                      className={s.topicThumb}
                      onError={(e) => {
                        e.currentTarget.src = `${API_URL}/static/img/default_news.svg`;
                      }}
                    />
                    <div>
                      <div className={s.topicTitle}>{n.title || "Без заголовка"}</div>
                      <div className={s.topicSource}>{sourceDisplay(n)}</div>
                    </div>
                  </div>
                );

                return isInternal ? (
                  <Link key={(n.id || n.slug || Math.random()) + "::topic-in"} to={href} style={{ textDecoration: "none" }}>
                    {card}
                  </Link>
                ) : (
                  <a
                    key={(n.id || n.slug || Math.random()) + "::topic-out"}
                    href={href}
                    target="_blank"
                    rel="noreferrer noopener"
                    style={{ textDecoration: "none" }}
                  >
                    {card}
                  </a>
                );
              })}
            </div>
          </>
        )}
      </article>

      {/* Правый сайдбар */}
      <aside className={s.sidebar}>
        <div className={s.sectionH}>Похожие новости</div>

        {sidebarItems.length === 0 ? (
          <div style={{ fontSize: 14, opacity: 0.7 }}>Ничего похожего не нашлось.</div>
        ) : (
          sidebarItems.map((n) => {
            const inner = buildInternalHref(n);
            const href = inner || n.link || "#";
            const isInternal = !!inner;

            const thumb =
              n.thumbnail ||
              n.cover_image ||
              n.image ||
              n.image_url ||
              `${API_URL}/static/img/default_news.svg`;

            const card = (
              <div className={s.relItem}>
                <img
                  src={thumb}
                  alt=""
                  className={s.relThumb}
                  onError={(e) => {
                    e.currentTarget.src = `${API_URL}/static/img/default_news.svg`;
                  }}
                />
                <div>
                  <div className={s.relTitle}>{n.title || "Без заголовка"}</div>
                  <div className={s.relSource}>{sourceDisplay(n)}</div>
                </div>
              </div>
            );

            return isInternal ? (
              <Link key={(n.id || n.slug || Math.random()) + "::in"} to={href} style={{ textDecoration: "none" }}>
                {card}
              </Link>
            ) : (
              <a
                key={(n.id || n.slug || Math.random()) + "::out"}
                href={href}
                target="_blank"
                rel="noreferrer noopener"
                style={{ textDecoration: "none" }}
              >
                {card}
              </a>
            );
          })
        )}
      </aside>
    </div>
  );
}
