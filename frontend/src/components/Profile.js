// ===== ФАЙЛ: frontend/src/components/Profile.js =====
// ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\frontend\\src\\components\\Profile.js
// НАЗНАЧЕНИЕ: Страница профиля авторизованного пользователя.
// ОПИСАНИЕ: Загружает данные профиля через API и отображает их в карточке
//            Materialize.

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

  if (loading) return <p>Загрузка профиля...</p>;
  if (!profile) return <p>Ошибка загрузки профиля</p>;

  return (
    <div className="container">
      <div className="card">
        <div className="card-content">
          <span className="card-title">Профиль</span>
          <p><b>Имя пользователя:</b> {profile.username}</p>
          <p><b>Email:</b> {profile.email}</p>
        </div>
      </div>
    </div>
  );
}

export default Profile;
