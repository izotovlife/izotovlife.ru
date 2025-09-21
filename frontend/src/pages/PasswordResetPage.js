// frontend/src/pages/PasswordResetPage.js
// Назначение: Форма для запроса восстановления пароля (отправка email).
// Путь: frontend/src/pages/PasswordResetPage.js

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../Api";

export default function PasswordResetPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    try {
      await api.post("/api/auth/password-reset/", { email });
      setMessage("Проверьте почту — мы отправили ссылку для восстановления.");
      setTimeout(() => navigate("/login"), 4000);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Ошибка при отправке письма. Попробуйте снова."
      );
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-[var(--bg-card)] p-6 rounded-xl shadow">
      <h1 className="text-xl font-bold mb-4 text-white">Восстановление пароля</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="email"
          placeholder="Ваш Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full p-2 rounded border border-gray-600 bg-transparent text-white"
        />
        {error && <div className="text-red-400 text-sm">{error}</div>}
        {message && <div className="text-green-400 text-sm">{message}</div>}
        <button
          type="submit"
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded text-white font-bold"
        >
          Отправить ссылку
        </button>
      </form>
    </div>
  );
}
