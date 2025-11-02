// Путь: frontend/src/pages/EditorDashboard.js
// Назначение: Личный кабинет редактора — модерация статей авторов.
// Что внутри (полный файл):
//   ✅ Загрузка очереди модерации через адаптер ../api/dashboards (listPendingSubmissions).
//   ✅ Действия: publishArticle(id) и requestChanges(id, message).
//   ✅ Поддержка и массивов, и пагинированных ответов (results).
//   ✅ Мини-отладка ошибок в консоль.
// Редкий кейс удаления (обязательно для корректной работы):
//   ❌ Удалены импорты fetchModerationQueue и reviewArticle из "../Api" — их там нет.
//   ✅ Заменены на функции адаптера из "../api/dashboards".

import React, { useEffect, useState } from "react";
import {
  listPendingSubmissions as fetchModerationQueue,
  publishArticle,
  requestChanges,
} from "../api/dashboards";

export default function EditorDashboard() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    loadArticles();
  }, []);

  async function loadArticles() {
    setLoading(true);
    setErr("");
    try {
      const data = await fetchModerationQueue();
      // Приведение к массиву: поддерживаем как [], так и {results: []}
      const list = Array.isArray(data) ? data : data?.results || [];
      setArticles(list);
    } catch (e) {
      console.error("Ошибка загрузки очереди модерации:", e);
      setArticles([]);
      setErr("Не удалось загрузить очередь модерации");
    } finally {
      setLoading(false);
    }
  }

  async function handlePublish(id) {
    try {
      await publishArticle(id);
      // Убираем статью из очереди
      setArticles((prev) => prev.filter((a) => a.id !== id));
      // Можно всплывашку
      // alert("Статья опубликована");
    } catch (e) {
      console.error("Ошибка публикации:", e);
      alert("Не удалось опубликовать статью");
    }
  }

  async function handleRevise(id) {
    const notes =
      prompt("Укажите причину/замечания для автора (это увидит автор):") || "";
    try {
      await requestChanges(id, notes);
      setArticles((prev) => prev.filter((a) => a.id !== id));
      // alert("Отправлено на доработку");
    } catch (e) {
      console.error("Ошибка отправки на доработку:", e);
      alert("Не удалось отправить на доработку");
    }
  }

  return (
    <div className="editor-dashboard max-w-3xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-white mb-6">Кабинет редактора</h1>

      {loading && <p className="text-gray-400">Загрузка...</p>}
      {!loading && err && (
        <p className="text-red-400 mb-4">{err}</p>
      )}

      {!loading && !err && articles.length === 0 ? (
        <p className="text-gray-400">Очередь пуста</p>
      ) : null}

      {!loading && !err && articles.length > 0 && (
        <div className="space-y-4">
          {articles.map((a) => (
            <div
              key={a.id}
              className="card border border-gray-700 rounded-lg p-4 bg-gray-900"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <h3 className="text-lg font-bold text-white break-words">
                    {a.title}
                  </h3>
                  <div className="text-sm text-gray-400 mt-1">
                    Автор:{" "}
                    <span className="text-gray-300">
                      {a.author_name ||
                        a.author?.display_name ||
                        a.author?.username ||
                        a.author ||
                        "—"}
                    </span>
                  </div>
                </div>
                {a.cover_image && (
                  // eslint-disable-next-line jsx-a11y/img-redundant-alt
                  <img
                    src={a.cover_image || a.cover || a.cover_url}
                    alt="Обложка"
                    className="max-h-20 rounded object-cover"
                    loading="lazy"
                  />
                )}
              </div>

              {a.content && (
                <div
                  className="prose prose-invert mt-3 max-w-none"
                  dangerouslySetInnerHTML={{ __html: a.content }}
                />
              )}

              <div className="mt-4 flex gap-3">
                <button
                  onClick={() => handlePublish(a.id)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                >
                  Опубликовать
                </button>
                <button
                  onClick={() => handleRevise(a.id)}
                  className="bg-yellow-500 hover:bg-yellow-600 text-black px-4 py-2 rounded"
                >
                  На доработку
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
