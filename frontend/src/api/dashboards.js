// Путь: frontend/src/api/dashboards.js
// Назначение: Совместимый клиент кабинетов (читатель/автор/редактор/публичные).
//
// Обновления (важно):
//   ✅ УБРАНЫ кандидаты с префиксом "/api/..." (они давали двойное /api в URL).
//   ✅ Расширен поиск профиля автора: /dashboards/author/page/<key>/, /authors/<key>/, /accounts/<id>/, /users/<id>/.
//   ✅ Расширен поиск опубликованных статей автора: пробуем author/author_id/user/user_id + PUBLISHED/published,
//      и общий список /news/?author=…
//   ✅ Добавлена отладка: __dashDbg.get/put/post — массивы всех попыток URL (видно в DevTools).
//
// НИЧЕГО не удалял из прежнего API — только поправил кандидаты и добавил отладку.

import { http } from "../Api";

// ---------- отладка ----------
export const __dashDbg = {
  get: [],
  post: [],
  put: [],
  reset() {
    this.get.length = 0;
    this.post.length = 0;
    this.put.length = 0;
  },
};

// ---------- утилиты ----------
async function tryGetSeq(urls) {
  for (const u of urls) {
    __dashDbg.get.push(u);
    try {
      const r = await http.get(u);
      if (r?.status >= 200 && r.status < 300) return r.data;
    } catch (_) {}
  }
  return null;
}
async function tryPostSeq(entries) {
  for (const [u, d, cfg] of entries) {
    __dashDbg.post.push(u);
    try {
      const r = await http.post(u, d, cfg || {});
      if (r?.status >= 200 && r.status < 300) return r.data;
    } catch (_) {}
  }
  return null;
}
async function tryPutSeq(entries) {
  for (const [u, d, cfg] of entries) {
    __dashDbg.put.push(u);
    try {
      const r = await http.put(u, d, cfg || {});
      if (r?.status >= 200 && r.status < 300) return r.data;
    } catch (_) {}
  }
  return null;
}
function toArray(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.results)) return data.results;
  return [];
}
function isFile(x) {
  return typeof File !== "undefined" && x instanceof File;
}

// ===================== ЧИТАТЕЛЬ =====================
export async function getMyFavorites() {
  const data = await tryGetSeq([
    "/dashboards/reader/favorites/",
    "/favorites/my/",
    "/favorites/",
    "/me/favorites/",
    "/news/favorites/", // на случай старой ручки
  ]);
  const arr = toArray(data);
  return arr
    .map((item) => ({
      url: item.url || item.link || item.href || "",
      title: item.title || item.name || "",
      slug: item.slug || "",
      source_name: item.source_name || item.source || "",
      source_logo_url: item.source_logo_url || item.source_logo || "",
      cover_url: item.cover_url || item.cover || item.image || "",
      created_at: item.created_at || item.added_at || null,
    }))
    .filter((x) => x.url);
}

export async function syncFavoriteSnapshot(snap) {
  await tryPostSeq([["/dashboards/reader/favorites/sync/", snap]]);
}

// ===================== АВТОР =====================
export async function listMyArticles(status = "") {
  const qs = status ? `?status=${encodeURIComponent(status)}` : "";
  const data = await tryGetSeq([
    `/dashboards/author/articles/${qs}`,
    `/news/author/articles/mine/${qs}`,
    `/news/author/articles/${qs}`,
  ]);
  return toArray(data);
}

export async function createArticle(payload) {
  const data = await tryPostSeq([
    ["/dashboards/author/articles/", payload],
    ["/news/author/articles/", payload],
  ]);
  if (!data) throw new Error("createArticle: нет подходящего эндпоинта");
  return data;
}

export async function updateArticle(id, payload) {
  const data = await tryPutSeq([
    [`/dashboards/author/articles/${id}/`, payload],
    [`/news/author/articles/${id}/`, payload],
  ]);
  if (!data) throw new Error("updateArticle: нет подходящего эндпоинта");
  return data;
}

export async function submitArticle(id) {
  const data = await tryPostSeq([
    [`/dashboards/author/articles/${id}/submit/`, {}],
    [`/news/author/articles/${id}/submit/`, {}],
  ]);
  if (!data) throw new Error("submitArticle: нет подходящего эндпоинта");
  return data; // {status: "pending"}
}

export async function withdrawArticle(id) {
  const data = await tryPostSeq([
    [`/dashboards/author/articles/${id}/withdraw/`, {}],
    [`/news/author/articles/${id}/withdraw/`, {}],
    [`/news/author/articles/${id}/revoke/`, {}],
  ]);
  if (!data) throw new Error("withdrawArticle: нет подходящего эндпоинта");
  return data; // {status: "draft"}
}

export async function listArticleComments(id) {
  const data = await tryGetSeq([
    `/dashboards/author/articles/${id}/comments/`,
    `/news/author/articles/${id}/comments/`,
  ]);
  return toArray(data);
}

export async function uploadAuthorImage(file) {
  const fd = new FormData();
  fd.append("image", file);
  const cfg = { headers: { "Content-Type": "multipart/form-data" } };
  const data = await tryPostSeq([
    ["/dashboards/author/upload-image/", fd, cfg],
    ["/news/upload-image/", fd, cfg],
  ]);
  if (!data?.url) throw new Error("uploadAuthorImage: нет подходящего эндпоинта");
  return data; // { url }
}

export async function setArticleCover(id, fileOrUrl) {
  async function putUrl(url) {
    const payloads = [{ cover: url }, { cover_image: url }, { cover_url: url }];
    for (const p of payloads) {
      const data = await tryPutSeq([
        [`/dashboards/author/articles/${id}/`, p],
        [`/news/author/articles/${id}/`, p],
      ]);
      if (data) return data;
    }
    return { cover: url };
  }

  if (isFile(fileOrUrl)) {
    const file = fileOrUrl;
    const fd1 = new FormData(); fd1.append("cover", file);
    const fd2 = new FormData(); fd2.append("image", file);
    const cfg = { headers: { "Content-Type": "multipart/form-data" } };

    let data =
      (await tryPostSeq([
        [`/dashboards/author/articles/${id}/cover/`, fd1, cfg],
        [`/news/author/articles/${id}/cover/`, fd1, cfg],
        [`/news/author/articles/${id}/upload-cover/`, fd2, cfg],
      ])) ||
      (await tryPutSeq([
        [`/dashboards/author/articles/${id}/`, fd1, cfg],
        [`/news/author/articles/${id}/`, fd1, cfg],
      ]));
    if (data) return data;

    const up = await uploadAuthorImage(file);
    return await putUrl(up.url);
  }

  if (typeof fileOrUrl === "string" && fileOrUrl.startsWith("http")) {
    return await putUrl(fileOrUrl);
  }
  throw new Error("setArticleCover: ожидается File или URL");
}

// ===================== РЕДАКТОР =====================
export async function listPendingSubmissions() {
  const data = await tryGetSeq([
    "/dashboards/editor/submissions/",
    "/news/moderation/queue/",
    "/moderation/queue/",
    "/editor/submissions/",
  ]);
  return toArray(data);
}

export async function publishArticle(id) {
  const data = await tryPostSeq([
    [`/dashboards/editor/submissions/${id}/publish/`, {}],
    ["/news/moderation/review/", { id, action: "publish" }],
    ["/moderation/review/", { id, action: "publish" }],
  ]);
  if (!data) throw new Error("publishArticle: нет подходящего эндпоинта");
  return data;
}

export async function requestChanges(id, message) {
  const data = await tryPostSeq([
    [`/dashboards/editor/submissions/${id}/request_changes/`, { message }],
    ["/news/moderation/review/", { id, action: "revise", message }],
    ["/moderation/review/", { id, action: "revise", message }],
  ]);
  if (!data) throw new Error("requestChanges: нет подходящего эндпоинта");
  return data;
}

// ===================== ПУБЛИЧНО (профиль + статьи) =====================
export async function getAuthorPublic(slugOrId) {
  const key = String(slugOrId || "");
  const isNum = /^\d+$/.test(key);

  const candidates = [
    `/dashboards/author/page/${encodeURIComponent(key)}/`,
    `/authors/${encodeURIComponent(key)}/`,
  ];
  if (isNum) {
    // только если похоже на ID — пробуем эти пути
    candidates.unshift(`/accounts/${key}/`, `/users/${key}/`);
  }

  const data = await tryGetSeq(candidates);
  if (!data) throw new Error("getAuthorPublic: не найден эндпоинт профиля");
  return data;
}

export async function listPublicArticlesByAuthor(authorIdent) {
  const qs = encodeURIComponent(String(authorIdent || ""));
  const candidates = [
    `/dashboards/author/articles/public/?author=${qs}`,
    // старые варианты «авторских статей»
    `/news/author/articles/?author=${qs}&status=PUBLISHED`,
    `/news/author/articles/?author=${qs}&status=published`,
    `/news/author/articles/?author_id=${qs}&status=PUBLISHED`,
    `/news/author/articles/?author_id=${qs}&status=published`,
    `/news/author/articles/?user=${qs}&status=PUBLISHED`,
    `/news/author/articles/?user=${qs}&status=published`,
    `/news/author/articles/?user_id=${qs}&status=PUBLISHED`,
    `/news/author/articles/?user_id=${qs}&status=published`,
    // общий фолбэк
    `/news/?author=${qs}&status=PUBLISHED`,
    `/news/?author=${qs}&status=published`,
    `/news/?author_id=${qs}&status=PUBLISHED`,
    `/news/?author_id=${qs}&status=published`,
  ];
  const data = await tryGetSeq(candidates);
  return toArray(data);
}
