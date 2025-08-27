// frontend/src/components/Profile.js
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
      <h2>Профиль</h2>
      <p><b>Имя пользователя:</b> {profile.username}</p>
      <p><b>Email:</b> {profile.email}</p>
    </div>
  );
}

export default Profile;
