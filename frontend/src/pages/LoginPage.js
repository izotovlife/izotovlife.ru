// frontend/src/pages/LoginPage.js
// Назначение: Форма входа.
// Суперпользователь → редирект в Django admin через одноразовый admin_url.
// Все остальные → используем redirect_url из бэка.
// Путь: frontend/src/pages/LoginPage.js

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { setToken, login, whoami, adminSessionLogin } from "../Api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      // 1. Авторизация: получаем JWT
      const res = await login(username, password);
      setToken(res.access);

      // 2. Проверяем, кто вошёл
      const meRes = await whoami();

      if (meRes.is_superuser) {
        // 3. Для суперпользователя — admin_url
        const sec = await adminSessionLogin();
        if (sec.admin_url) {
          window.location.href = sec.admin_url;
        } else {
          setError("Не удалось получить ссылку для входа в админку.");
        }
      } else {
        // 4. Для всех остальных — используем redirect_url из бэка
        if (meRes.redirect_url) {
          navigate(meRes.redirect_url);
        } else {
          navigate("/");
        }
      }
    } catch (err) {
      console.error("Ошибка входа:", err);
      setError(
        err?.response?.data?.detail || err.message || "Ошибка входа. Попробуйте снова."
      );
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-[var(--bg-card)] p-6 rounded-xl shadow">
      <h1 className="text-xl font-bold mb-4 text-white">Вход</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          placeholder="Логин или Email"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-2 rounded border border-gray-600 bg-transparent text-white"
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-2 rounded border border-gray-600 bg-transparent text-white"
        />
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <button
          type="submit"
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded text-white font-bold"
        >
          Войти
        </button>
      </form>
    </div>
  );
}
