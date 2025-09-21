// frontend/src/pages/PasswordResetConfirmPage.js
// Назначение: Ввод нового пароля по ссылке из письма восстановления.
// Путь: frontend/src/pages/PasswordResetConfirmPage.js

import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../Api";

export default function PasswordResetConfirmPage() {
  const { uid, token } = useParams();
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (password !== password2) {
      setError("Пароли не совпадают.");
      return;
    }

    try {
      await api.post(`/api/auth/password-reset-confirm/${uid}/${token}/`, {
        password,
      });
      setMessage("Пароль успешно изменён. Перенаправляем на вход...");
      setTimeout(() => navigate("/login"), 3000);
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Ошибка при изменении пароля. Попробуйте снова."
      );
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-[var(--bg-card)] p-6 rounded-xl shadow">
      <h1 className="text-xl font-bold mb-4 text-white">Новый пароль</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="password"
          placeholder="Новый пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-2 rounded border border-gray-600 bg-transparent text-white"
        />
        <input
          type="password"
          placeholder="Повторите пароль"
          value={password2}
          onChange={(e) => setPassword2(e.target.value)}
          className="w-full p-2 rounded border border-gray-600 bg-transparent text-white"
        />
        {error && <div className="text-red-400 text-sm">{error}</div>}
        {message && <div className="text-green-400 text-sm">{message}</div>}
        <button
          type="submit"
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded text-white font-bold"
        >
          Сохранить пароль
        </button>
      </form>
    </div>
  );
}
