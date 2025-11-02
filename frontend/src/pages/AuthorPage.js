// Путь: frontend/src/pages/AuthorPage.js
// Назначение: Публичная страница автора (фото/обложка, био, список опубликованных статей).
// Что внутри (полный файл):
//   ✅ Фолбэки к разным ручкам бэка через адаптер ../api/dashboards.
//   ✅ DEBUG-блок (?debug=1) — показывает, какие URL пробовали.
//   ✅ Авто-редирект: если в /author/:id приходит служебное слово
//      (dashboard/editor/reader/me), уходим на кабинеты:
//        /author/dashboard  →  /dashboard/author
//        /author/editor     →  /dashboard/editor
//        /author/reader     →  /dashboard/reader
//        /author/me         →  /dashboard/author
//   ⚠️ Ничего лишнего не удалено — добавил только безопасные проверки и редирект.

import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link, useSearchParams, useNavigate } from "react-router-dom";
import { getAuthorPublic, listPublicArticlesByAuthor, __dashDbg } from "../api/dashboards";

function formatDate(iso) {
  if (!iso) return "Без даты";
  try { return new Date(iso).toLocaleDateString(); } catch { return "Без даты"; }
}
function pickCover(a) {
  return a?.cover || a?.cover_image || a?.cover_url || "";
}
function pickName(author) {
  const fn = (author?.first_name || "").trim();
  const ln = (author?.last_name || "").trim();
  const full = [fn, ln].filter(Boolean).join(" ");
  return full || author?.display_name || author?.username || author?.name || author?.slug || "Автор";
}
function buildDetailHref(a) {
  const slug = a?.slug;
  if (!slug) return "#";
  return `/a/${slug}`; // при желании можно вернуть /news/<cat>/<slug>
}

export default function AuthorPage() {
  const { id: routeParam } = useParams(); // сейчас маршрут вида /author/:id
  const [sp] = useSearchParams();
  const navigate = useNavigate();
  const debug = sp.get("debug") === "1";

  const [author, setAuthor] = useState(null);
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  // распознаём «служебные» слова
  const routeKind = useMemo(() => {
    const v = String(routeParam || "").toLowerCase();
    if (["dashboard", "me"].includes(v)) return "author-dashboard";
    if (v === "editor") return "editor-dashboard";
    if (v === "reader") return "reader-dashboard";
    return null;
  }, [routeParam]);

  // моментальный редирект с «служебных» путей
  useEffect(() => {
    if (!routeKind) return;
    const map = {
      "author-dashboard": "/dashboard/author/",
      "editor-dashboard": "/dashboard/editor/",
      "reader-dashboard": "/dashboard/reader/",
    };
    const to = map[routeKind];
    if (to) navigate(to, { replace: true });
  }, [routeKind, navigate]);

  useEffect(() => {
    if (routeKind) return; // если это служебный путь — данных автора не грузим

    let cancelled = false;
    (async () => {
      __dashDbg.reset();
      setLoading(true);
      setErr("");

      try {
        // 1) Профиль (адаптер сам подберёт нужный эндпоинт)
        const profile = await getAuthorPublic(routeParam);
        if (cancelled) return;
        setAuthor(profile);

        // 2) Надёжный идентификатор для статей
        const paramIsNumber = /^\d+$/.test(String(routeParam || ""));
        const authorIdent = paramIsNumber ? routeParam : (profile?.id ?? profile?.slug ?? routeParam);

        // 3) Опубликованные статьи автора (c фолбэками по параметрам/статусам)
        const arts = await listPublicArticlesByAuthor(authorIdent);
        if (!cancelled) setArticles(Array.isArray(arts) ? arts : arts?.results || []);
      } catch (e) {
        console.error("Ошибка загрузки автора:", e);
        if (!cancelled) {
          setAuthor(null);
          setArticles([]);
          setErr(e?.message || "Не удалось загрузить данные автора");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [routeParam, routeKind]);

  if (routeKind) {
    // пока идёт replace-редирект — отрисуем пустой экран
    return null;
  }

  if (loading) return <div className="p-4">Загрузка…</div>;

  return (
    <div className="max-w-4xl mx-auto p-4">
      {/* DEBUG блок (включается ?debug=1) */}
      {debug && (
        <div className="mb-4 p-3 rounded border border-yellow-600 text-yellow-300 bg-black/40">
          <div className="font-semibold mb-1">DEBUG /author/:id</div>
          <div><b>routeParam:</b> {String(routeParam)}</div>
          <div><b>routeKind:</b> {String(routeKind)}</div>
          <div className="mt-2">
            <b>GET попытки:</b>
            <ul className="list-disc pl-5">
              {__dashDbg.get.map((u, i) => <li key={`g${i}`}>{u}</li>)}
            </ul>
          </div>
          {__dashDbg.post.length > 0 && (
            <div className="mt-2">
              <b>POST попытки:</b>
              <ul className="list-disc pl-5">
                {__dashDbg.post.map((u, i) => <li key={`p${i}`}>{u}</li>)}
              </ul>
            </div>
          )}
          {__dashDbg.put.length > 0 && (
            <div className="mt-2">
              <b>PUT попытки:</b>
              <ul className="list-disc pl-5">
                {__dashDbg.put.map((u, i) => <li key={`u${i}`}>{u}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {!author ? (
        <div className="p-4">{err || "Автор не найден"}</div>
      ) : (
        <>
          {/* Обложка автора */}
          {(author.cover || author.header || author.banner) && (
            <div className="mb-4">
              <img
                src={author.cover || author.header || author.banner}
                alt=""
                className="w-full h-44 object-cover rounded-md"
                loading="lazy"
              />
            </div>
          )}

          {/* Профиль */}
          <div className="flex items-center gap-4 mb-6">
            {(author.avatar || author.photo || author.image) && (
              <img
                src={author.avatar || author.photo || author.image}
                alt={pickName(author)}
                className="w-20 h-20 rounded-full object-cover"
                loading="lazy"
              />
            )}
            <div className="min-w-0">
              <h1 className="text-2xl font-bold truncate">{pickName(author)}</h1>
              {(author.bio || author.description) && (
                <p className="text-gray-400">{author.bio || author.description}</p>
              )}
            </div>
          </div>

          {/* Статьи */}
          <h2 className="text-xl font-semibold mb-3">Статьи автора</h2>
          {articles.length === 0 ? (
            <p className="text-gray-500">У этого автора пока нет опубликованных статей.</p>
          ) : (
            <div className="space-y-4">
              {articles.map((a) => {
                const cov = pickCover(a);
                return (
                  <div key={a.id || a.slug} className="p-4 border rounded hover:shadow">
                    {cov && (
                      <img
                        src={cov}
                        alt=""
                        className="w-full h-40 object-cover mb-2 rounded"
                        loading="lazy"
                      />
                    )}
                    <Link
                      to={buildDetailHref(a)}
                      className="text-lg font-bold text-blue-600 hover:underline"
                    >
                      {a.title}
                    </Link>
                    <div className="text-sm text-gray-500">{formatDate(a.published_at)}</div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
