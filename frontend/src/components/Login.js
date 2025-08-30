// frontend/src/components/Login.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { AuthAPI, AccountsAPI } from "../api";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      // используем AuthAPI.login
      const tokens = await AuthAPI.login(username, password);

      // получаем профиль
      const profileRes = await AccountsAPI.getProfile();

      if (profileRes.data.is_superuser) {
        // если суперпользователь → запрос одноразовой ссылки
        const linkRes = await api.post("accounts/superuser-admin-link/");
        window.location.href = linkRes.data.url; // редиректим в админку
      } else {
        navigate("/profile");
      }
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
