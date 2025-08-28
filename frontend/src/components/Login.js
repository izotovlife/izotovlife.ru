// ===== ФАЙЛ: frontend/src/components/Login.js =====
// ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\frontend\\src\\components\\Login.js
// НАЗНАЧЕНИЕ: Общая форма входа для авторов и администратора.
// ОПИСАНИЕ: Отправляет логин и пароль на backend; суперпользователь получает
//            одноразовую ссылку в админку, остальные — JWT токены.

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const res = await api.post("accounts/login/", { username, password });

      if (res.data.admin_url) {
        window.location.href = res.data.admin_url;
        return;
      }

      localStorage.setItem("access", res.data.access);
      localStorage.setItem("refresh", res.data.refresh);
      navigate("/profile");
    } catch (err) {
      console.error("Ошибка входа:", err);
      setError("Неверное имя пользователя или пароль");
    }
  };

  return (
    <div className="container">
      <h2>Вход</h2>
      <form onSubmit={handleSubmit}>
        <div className="input-field">
          <input
            type="text"
            placeholder="Имя пользователя"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="input-field">
          <input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p style={{ color: "red" }}>{error}</p>}
        <button type="submit" className="btn">Войти</button>
      </form>
    </div>
  );
}

export default Login;
