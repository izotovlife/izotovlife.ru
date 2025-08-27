// frontend/src/components/Profile.js
// Путь: frontend/src/components/Profile.js
// Назначение: просмотр и редактирование профиля автора.

import React, { useEffect, useState } from "react";
import api from "../api";

function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchProfile() {
      try {
        const res = await api.get("accounts/profile/");
        setProfile(res.data);
      } catch (err) {
        console.error("Ошибка загрузки профиля:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchProfile();
  }, []);

  const handleChange = (e) => {
    setProfile({ ...profile, [e.target.name]: e.target.value });
  };

  const handleFile = (e) => {
    setProfile({ ...profile, photo: e.target.files[0] });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("first_name", profile.first_name || "");
    formData.append("last_name", profile.last_name || "");
    formData.append("bio", profile.bio || "");
    if (profile.photo instanceof File) {
      formData.append("photo", profile.photo);
    }
    try {
      const res = await api.patch("accounts/profile/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setProfile(res.data);
      alert("Профиль обновлён");
    } catch (err) {
      console.error("Ошибка обновления профиля:", err);
    }
  };

  if (loading) return <p>Загрузка профиля...</p>;
  if (!profile) return <p>Ошибка загрузки профиля</p>;

  return (
    <div className="container">
      <h2>Профиль</h2>
      <p><b>Имя пользователя:</b> {profile.username}</p>
      <p><b>Email:</b> {profile.email}</p>
      <form onSubmit={handleSubmit}>
        <div className="input-field">
          <input
            name="first_name"
            value={profile.first_name || ""}
            onChange={handleChange}
          />
          <label className="active" htmlFor="first_name">Имя</label>
        </div>
        <div className="input-field">
          <input
            name="last_name"
            value={profile.last_name || ""}
            onChange={handleChange}
          />
          <label className="active" htmlFor="last_name">Фамилия</label>
        </div>
        <div className="input-field">
          <textarea
            name="bio"
            className="materialize-textarea"
            value={profile.bio || ""}
            onChange={handleChange}
          ></textarea>
          <label className="active" htmlFor="bio">Описание</label>
        </div>
        <div className="file-field input-field">
          <div className="btn">
            <span>Фото</span>
            <input type="file" onChange={handleFile} />
          </div>
          <div className="file-path-wrapper">
            <input className="file-path validate" type="text" />
          </div>
        </div>
        <button className="btn" type="submit">Сохранить</button>
      </form>
    </div>
  );
}

export default Profile;
