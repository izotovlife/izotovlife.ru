// Путь: frontend/src/pages/AuthorDashboard.js
// Назначение: Кабинет автора (создание/редактирование статей + список).
// Важные изменения для фикса «поле заголовка не кликается»:
//   • МОДАЛКИ РАЗМОНТИРУЮТСЯ: {previewOpen && <PreviewModal .../>} и {publishOpen && <PublishDialog .../>}
//     — так никакой бекдроп не сможет накрыть поле, когда модалка закрыта.
//   • На инпуте заголовка оставлен контролируемый режим + autoSave, можно добавить autoFocus.
//
// Прочее: логика сохранения/автосохранения/публикации не трогалась.

import React, { useCallback, useEffect, useRef, useState } from "react";
import "./AuthorDashboard.css";
import ZenEditor from "../components/zen/ZenEditor";
import PreviewModal from "../components/zen/PreviewModal";
import PublishDialog from "../components/zen/PublishDialog";

import {
  listMyArticles as fetchMyArticles,
  createArticle,
  updateArticle,
  submitArticle,
  withdrawArticle,
  uploadAuthorImage,
  setArticleCover,
} from "../api/dashboards";
import { fetchCategories } from "../Api";

const RU_STATUS = { draft: "Черновик", pending: "На модерации", published: "Опубликовано" };
const isDraft = (s) => s === "draft" || s === "Черновик";
const isPending = (s) => s === "pending" || s === "На модерации";

const LS_KEY = "authorDraft_v1";

/** Универсально достаём id из разных форм ответов бэкенда */
const pickId = (x) =>
  x?.id ??
  x?.pk ??
  x?.uuid ??
  x?.data?.id ??
  x?.data?.pk ??
  x?.article?.id ??
  x?.result?.id ??
  null;

export default function AuthorDashboard() {
  const [showForm, setShowForm] = useState(true);

  const [articles, setArticles] = useState([]);
  const [categoriesList, setCategoriesList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [editingId, setEditingId] = useState(null);
  const [title, setTitle] = useState("");
  const [categories, setCategories] = useState([]);
  const [tags, setTags] = useState([]);

  const [coverFile, setCoverFile] = useState(null);
  const [coverPreview, setCoverPreview] = useState("");

  const [contentJson, setContentJson] = useState(null);
  const [contentHtml, setContentHtml] = useState("");

  const [previewOpen, setPreviewOpen] = useState(false);
  const [publishOpen, setPublishOpen] = useState(false);

  const [autoSaveState, setAutoSaveState] = useState({ phase: "idle", ts: null });
  const savingRef = useRef(false);
  const dirtyRef = useRef(false);
  const lastPayloadRef = useRef("");

  const formatTime = (ts) => {
    if (!ts) return "";
    const d = new Date(ts);
    const two = (n) => (n < 10 ? "0" + n : n);
    return `${two(d.getHours())}:${two(d.getMinutes())}`;
  };

  const loadArticles = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchMyArticles();
      const items = Array.isArray(data) ? data : data?.results || [];
      setArticles(items);
    } catch (e) {
      console.error(e);
      setError("Ошибка загрузки статей");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadCategories = useCallback(async () => {
    try {
      const data = await fetchCategories();
      setCategoriesList(Array.isArray(data) ? data : data?.results || []);
    } catch (e) {
      console.error("Ошибка категорий", e);
    }
  }, []);

  useEffect(() => {
    loadArticles();
    loadCategories();
  }, [loadArticles, loadCategories]);

  useEffect(() => {
    if (showForm) document.body.classList.add("zen-no-scroll");
    return () => document.body.classList.remove("zen-no-scroll");
  }, [showForm]);

  const samePayload = (payload) => {
    const snap = JSON.stringify(payload);
    if (snap === lastPayloadRef.current) return true;
    lastPayloadRef.current = snap;
    return false;
  };

  /** Создание/обновление. Возвращает надёжный ID. */
  const handleSave = useCallback(
    async (e, { forceDraft = false, forceCreate = false } = {}) => {
      e?.preventDefault?.();

      const payload = {
        title,
        body: contentHtml,
        content: contentHtml,
        content_html: contentHtml,
        content_json: contentJson ? JSON.stringify(contentJson) : null,
        meta_categories: categories,
        categories,
        tags,
        status: forceDraft ? "draft" : undefined,
        meta: { editor: "editorjs" },
      };

      // Если записи ещё нет — всегда создаём
      if (!editingId) {
        const created = await createArticle(payload);
        const newId = pickId(created);
        setArticles((prev) => (newId ? [{ ...(created || {}), id: newId }, ...prev] : prev));
        if (newId) setEditingId(newId);
        lastPayloadRef.current = JSON.stringify(payload);

        if (coverFile && newId) {
          try { await setArticleCover(newId, coverFile); } catch (err) { console.warn(err); }
        }
        await loadArticles();
        return newId;
      }

      // Есть запись: обновляем только при изменениях или при явном принуждении
      if (!forceCreate && samePayload(payload)) return editingId;

      const saved = await updateArticle(editingId, payload);
      const savedId = pickId(saved) || editingId;
      setArticles((prev) => prev.map((it) => (pickId(it) === savedId ? { ...it, ...(saved || {}) } : it)));

      if (coverFile && savedId) {
        try { await setArticleCover(savedId, coverFile); } catch (err) { console.warn(err); }
      }
      await loadArticles();
      return savedId;
    },
    [editingId, title, contentHtml, contentJson, categories, tags, coverFile, loadArticles]
  );

  const autoSaveNow = useCallback(async () => {
    try {
      const d = { title, tags, categories, coverPreview, contentJson, contentHtml };
      localStorage.setItem(LS_KEY, JSON.stringify(d));
    } catch {}

    dirtyRef.current = true;
    if (savingRef.current) return;

    while (dirtyRef.current) {
      dirtyRef.current = false;
      savingRef.current = true;
      setAutoSaveState({ phase: "saving", ts: null });
      try {
        await handleSave({ preventDefault() {} }, { forceDraft: true });
        setAutoSaveState({ phase: "saved", ts: Date.now() });
      } catch {
        setAutoSaveState({ phase: "error", ts: Date.now() });
      } finally {
        savingRef.current = false;
      }
    }
  }, [title, tags, categories, coverPreview, contentJson, contentHtml, handleSave]);

  useEffect(() => {
    if (!showForm || editingId) return;
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (!raw) return;
      const d = JSON.parse(raw);
      setTitle(d.title || "");
      setTags(d.tags || []);
      setCategories(d.categories || []);
      setCoverPreview(d.coverPreview || "");
      setContentJson(d.contentJson || null);
      setContentHtml(d.contentHtml || "");
    } catch {}
  }, [showForm, editingId]);

  async function handleCancel() {
    try { await handleSave({ preventDefault() {} }, { forceDraft: true }); }
    catch (e) { console.warn("Отмена: сохранить как черновик не удалось", e); }
    finally { resetForm(); }
  }

  /** Публикация: надёжно получаем ID и только затем выставляем категории/обложку и submit */
  async function confirmPublish({ categoryIds, cover }) {
    try {
      // 1) пробуем получить ID от сохранения (с принуждением)
      let articleId = await handleSave(null, { forceCreate: true });

      // 2) fallback — текущий editingId
      if (!articleId) articleId = editingId;

      // 3) крайний случай — свежий список и подбор по заголовку
      if (!articleId) {
        const data = await fetchMyArticles();
        const items = Array.isArray(data) ? data : data?.results || [];
        const byTitle =
          items.find((it) => (it?.title || "").trim() === (title || "").trim()) || items[0] || null;
        articleId = pickId(byTitle);
      }

      if (!articleId) {
        alert("Не удалось определить ID статьи");
        return;
      }

      if (Array.isArray(categoryIds) && categoryIds.length) {
        await updateArticle(articleId, { meta_categories: categoryIds, categories: categoryIds });
      }

      if (cover?.kind === "file" && cover.file) {
        await setArticleCover(articleId, cover.file);
      } else if (cover?.kind === "url" && cover.url) {
        try { await updateArticle(articleId, { cover: cover.url, cover_url: cover.url }); }
        catch (e) { console.warn("Обновление обложки по URL не поддержано сервером:", e); }
      }

      await submitArticle(articleId);
      await loadArticles();
      alert("Отправлено на модерацию");
      setPublishOpen(false);
      resetForm();
    } catch (e) {
      console.error(e);
      alert("Не удалось опубликовать");
    }
  }

  async function handleWithdrawArticle(id) {
    try {
      const res = await withdrawArticle(id);
      const newStatus = res?.status || "draft";
      setArticles((prev) => prev.map((a) => (pickId(a) === id ? { ...a, status: newStatus } : a)));
    } catch {
      setError("Не удалось отозвать статью");
    }
  }

  function resetForm() {
    setShowForm(false);
    setEditingId(null);
    setTitle("");
    setCategories([]);
    setTags([]);
    setCoverFile(null);
    setCoverPreview("");
    setContentJson(null);
    setContentHtml("");
    try { localStorage.removeItem(LS_KEY); } catch {}
  }

  // ====== UI ======
  if (showForm) {
    return (
      <div className="zen-fullscreen">
        <div className="zen-topbar">
          <div className="zen-topbar__left">
            <button onClick={handleCancel} className="btn btn--ghost">Отмена</button>
          </div>
          <div className="zen-topbar__center">
            <span className="zen-topbar__title">Новая статья</span>
          </div>
          <div className="zen-topbar__right">
            <span className="zen-topbar__status" title="Статус автосохранения">
              {autoSaveState.phase === "saving" && "Сохраняю…"}
              {autoSaveState.phase === "saved" && `Сохранено ${formatTime(autoSaveState.ts)}`}
              {autoSaveState.phase === "error" && "Ошибка сохранения"}
            </span>
            <button onClick={() => setPreviewOpen(true)} className="btn btn--ghost">Предпросмотр</button>
            <button onClick={() => setPublishOpen(true)} className="btn btn--accent">Опубликовать</button>
          </div>
        </div>

        <div className="zen-workarea">
          <div className="zen-compose">
            <input
              type="text"
              placeholder="Заголовок"
              value={title}
              onChange={(e) => { setTitle(e.target.value); autoSaveNow(); }}
              className="zen-title-input"
              required
              autoFocus
              autoComplete="off"
            />
            <ZenEditor
              initialJson={contentJson}
              initialHtml={contentHtml}
              onUploadImage={uploadAuthorImage}
              onChange={({ json, html }) => {
                setContentJson(json);
                setContentHtml(html);
                autoSaveNow();
              }}
            />
          </div>
        </div>

        {/* ВАЖНО: модалки размонтируются, когда закрыты */}
        {previewOpen && (
          <PreviewModal
            open={previewOpen}
            onClose={() => setPreviewOpen(false)}
            title={title}
            cover={coverPreview}
            html={contentHtml}
            contentJson={contentJson}
          />
        )}

        {publishOpen && (
          <PublishDialog
            open={publishOpen}
            onClose={() => setPublishOpen(false)}
            categoriesList={categoriesList}
            initialCategories={categories}
            currentCover={coverPreview}
            contentJson={contentJson}
            contentHtml={contentHtml}
            onConfirm={confirmPublish}
          />
        )}
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-6 text-white">
      <h1 className="text-2xl font-bold mb-4">Кабинет автора</h1>

      {error && <div className="text-red-400 mb-4">{error}</div>}

      <button
        onClick={() => setShowForm(true)}
        className="mb-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
      >
        Создать статью
      </button>

      {loading ? (
        <div>Загрузка…</div>
      ) : articles.length === 0 ? (
        <div>У вас пока нет статей.</div>
      ) : (
        <ul className="space-y-3">
          {articles.map((a) => {
            const id = pickId(a);
            return (
              <li key={id} className="p-3 border border-gray-700 rounded bg-[var(--card-bg,#0f1420)]">
                <div className="flex justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="font-bold truncate">{a.title}</h3>
                    <p className="text-sm text-gray-400">Статус: {RU_STATUS[a.status] || a.status}</p>
                  </div>
                  {(a.cover || a.cover_image || a.cover_url) && (
                    <img
                      src={a.cover || a.cover_image || a.cover_url}
                      alt="Обложка"
                      className="max-h-20 rounded object-cover"
                    />
                  )}
                </div>
                <div className="mt-3 flex gap-2">
                  {isDraft(a.status) && (
                    <>
                      <button
                        onClick={() => {
                          setShowForm(true);
                          setEditingId(id);
                          setTitle(a.title || "");
                          const meta = Array.isArray(a.meta_categories)
                            ? a.meta_categories
                            : Array.isArray(a.categories)
                            ? a.categories.map((c) => (typeof c === "object" ? c.id ?? c.slug ?? c : c))
                            : [];
                          setCategories(meta);
                          const tg = Array.isArray(a.tags)
                            ? a.tags
                            : typeof a.tags === "string"
                            ? a.tags.split(",").map((x) => x.trim()).filter(Boolean)
                            : [];
                          setTags(tg);
                          const raw = a.content_json || a.body_json || null;
                          if (raw) {
                            try {
                              const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
                              setContentJson(parsed);
                              setContentHtml(a.body || a.content || "");
                            } catch {
                              setContentJson(null);
                              setContentHtml(a.body || a.content || "");
                            }
                          } else {
                            setContentJson(null);
                            setContentHtml(a.body || a.content || "");
                          }
                          setCoverFile(null);
                          setCoverPreview(a.cover || a.cover_image || a.cover_url || "");
                        }}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded"
                      >
                        Редактировать
                      </button>
                      <button
                        onClick={async () => {
                          try { await submitArticle(id); await loadArticles(); }
                          catch { alert("Не удалось отправить"); }
                        }}
                        className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 rounded text-black"
                      >
                        Отправить
                      </button>
                    </>
                  )}
                  {isPending(a.status) && (
                    <button
                      onClick={() => handleWithdrawArticle(id)}
                      className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded"
                    >
                      Отозвать
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
