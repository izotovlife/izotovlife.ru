// frontend/src/components/Profile.js
// Просмотр и редактирование профиля автора (режимы: view/edit)

import React, { useEffect, useMemo, useState } from "react";
import api from "../api";

function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const [edit, setEdit] = useState(false);
  const [form, setForm] = useState({ first_name: "", last_name: "", bio: "" });
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // загрузка профиля
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await api.get("accounts/profile/");
        if (!mounted) return;
        setProfile(res.data);
        setForm({
          first_name: res.data.first_name ?? "",
          last_name: res.data.last_name ?? "",
          bio: res.data.bio ?? "",
        });
      } catch (err) {
        console.error("Ошибка загрузки профиля:", err);
      } finally {
        setLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, []);

  // превью выбранного файла
  useEffect(() => {
    if (!file) { setPreview(null); return; }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const avatarSrc = useMemo(() => {
    // сервер отдаёт абсолютный URL (см. SerializerMethodField на бэке)
    return preview || profile?.photo || null;
  }, [preview, profile]);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((s) => ({ ...s, [name]: value }));
  };

  const onFile = (e) => {
    const f = e.target.files?.[0];
    setFile(f || null);
  };

  const onEdit = () => {
    setEdit(true);
    setError(null);
  };

  const onCancel = () => {
    setEdit(false);
    setError(null);
    setFile(null);
    setPreview(null);
    if (profile) {
      setForm({
        first_name: profile.first_name ?? "",
        last_name: profile.last_name ?? "",
        bio: profile.bio ?? "",
      });
    }
  };

  const onSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      let res;
      if (file) {
        const fd = new FormData();
        fd.append("first_name", form.first_name);
        fd.append("last_name", form.last_name);
        fd.append("bio", form.bio);
        fd.append("photo", file);
        // Важно: не ставим Content-Type — axios сам проставит multipart границы
        res = await api.patch("accounts/profile/", fd);
      } else {
        res = await api.patch("accounts/profile/", form);
      }
      setProfile(res.data);
      setEdit(false);
      setFile(null);
      setPreview(null);
    } catch (err) {
      console.error("Ошибка обновления профиля:", err);
      setError(err?.response?.data || "Не удалось сохранить изменения");
    } finally {
      setSaving(false);
    }
  };

  const onRemovePhoto = async () => {
    try {
      const res = await api.patch("accounts/profile/", { photo: null });
      setProfile(res.data);
      setFile(null);
      setPreview(null);
    } catch (err) {
      console.error("Ошибка удаления фото:", err);
      setError(err?.response?.data || "Не удалось удалить фото");
    }
  };

  if (loading) return <p>Загрузка профиля…</p>;
  if (!profile) return <p>Ошибка загрузки профиля</p>;

  return (
    <div className="container" style={{ maxWidth: 720 }}>
      <h2>Профиль</h2>

      {/* Режим просмотра (по умолчанию) */}
      {!edit && (
        <>
          <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
            <div>
              {avatarSrc ? (
                <img
                  src={avatarSrc}
                  alt="avatar"
                  style={{ width: 132, height: 132, borderRadius: "50%", objectFit: "cover", border: "1px solid #eee" }}
                />
              ) : (
                <div style={{ width: 132, height: 132, borderRadius: "50%", background: "#f2f2f2", display: "grid", placeItems: "center" }}>
                  <span>Нет фото</span>
                </div>
              )}
            </div>

            <div style={{ flex: 1 }}>
              <p><b>Имя пользователя:</b> {profile.username}</p>
              <p><b>Email:</b> {profile.email}</p>
              <p><b>Имя:</b> {profile.first_name || "—"}</p>
              <p><b>Фамилия:</b> {profile.last_name || "—"}</p>
              <p><b>О себе:</b> {profile.bio || "—"}</p>

              <button className="btn" onClick={onEdit}>Редактировать</button>
            </div>
          </div>
        </>
      )}

      {/* Режим редактирования */}
      {edit && (
        <form onSubmit={onSave}>
          <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
            <div>
              {avatarSrc ? (
                <img
                  src={avatarSrc}
                  alt="avatar"
                  style={{ width: 132, height: 132, borderRadius: "50%", objectFit: "cover", border: "1px solid #eee" }}
                />
              ) : (
                <div style={{ width: 132, height: 132, borderRadius: "50%", background: "#f2f2f2", display: "grid", placeItems: "center" }}>
                  <span>Нет фото</span>
                </div>
              )}
              <div className="file-field input-field" style={{ marginTop: 8 }}>
                <div className="btn">
                  <span>Фото</span>
                  <input type="file" accept="image/*" onChange={onFile} />
                </div>
                <div className="file-path-wrapper">
                  <input className="file-path validate" type="text" readOnly />
                </div>
                {profile.photo && !file && (
                  <button type="button" className="btn-flat" onClick={onRemovePhoto} style={{ marginTop: 8 }}>
                    Удалить текущее фото
                  </button>
                )}
              </div>
            </div>

            <div style={{ flex: 1 }}>
              <div className="input-field">
                <input id="first_name" name="first_name" value={form.first_name} onChange={onChange} />
                <label className="active" htmlFor="first_name">Имя</label>
              </div>

              <div className="input-field">
                <input id="last_name" name="last_name" value={form.last_name} onChange={onChange} />
                <label className="active" htmlFor="last_name">Фамилия</label>
              </div>

              <div className="input-field">
                <textarea
                  id="bio"
                  name="bio"
                  className="materialize-textarea"
                  value={form.bio}
                  onChange={onChange}
                  rows={4}
                />
                <label className="active" htmlFor="bio">Описание</label>
              </div>

              {error && (
                <div style={{ color: "crimson", margin: "6px 0" }}>
                  {typeof error === "string" ? error : JSON.stringify(error)}
                </div>
              )}

              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button className="btn" type="submit" disabled={saving}>
                  {saving ? "Сохранение…" : "Сохранить"}
                </button>
                <button className="btn-flat" type="button" onClick={onCancel} disabled={saving}>
                  Отмена
                </button>
              </div>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}

export default Profile;
