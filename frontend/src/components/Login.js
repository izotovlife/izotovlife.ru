// ===== ФАЙЛ: frontend/src/components/Login.js =====
// ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\frontend\\src\\components\\Login.js
// НАЗНАЧЕНИЕ: Форма входа для авторов и редакторов.
// ОПИСАНИЕ: Отправляет логин и пароль на backend и сохраняет JWT токены.

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
    setError(""); // очищаем ошибки

    try {
      const res = await api.post("token/", { username, password });

      // сохраняем токены в localStorage
      localStorage.setItem("access", res.data.access);
      localStorage.setItem("refresh", res.data.refresh);

      // переходим на страницу профиля
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
