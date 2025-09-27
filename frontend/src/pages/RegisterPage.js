// frontend/src/pages/RegisterPage.js
// Назначение: Форма регистрации нового пользователя.
// Добавлены функции генерации, показа/скрытия и копирования сложного пароля.
// После успешной регистрации выводится сообщение "Проверьте почту для активации аккаунта".
// Путь: frontend/src/pages/RegisterPage.js

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register } from "../Api";

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Генерация случайного пароля
  const generatePassword = () => {
    const length = 16;
    const charset =
      "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+[]{}<>?";
    let pass = "";
    const array = new Uint32Array(length);
    window.crypto.getRandomValues(array);
    for (let i = 0; i < length; i++) {
      pass += charset[array[i] % charset.length];
    }
    setPassword(pass);
  };

  // Копирование пароля
  const copyPassword = async () => {
    try {
      await navigator.clipboard.writeText(password);
      setMessage("Пароль скопирован в буфер обмена!");
    } catch (err) {
      setError("Не удалось скопировать пароль");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    try {
      await register({ username, email, password });
      setMessage("Регистрация прошла успешно! Проверьте почту для активации аккаунта.");
      // Можно перенаправить через несколько секунд:
      setTimeout(() => navigate("/login"), 4000);
    } catch (err) {
      console.error("Ошибка регистрации:", err);
      setError(err?.response?.data || "Ошибка регистрации. Попробуйте снова.");
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 bg-[var(--bg-card)] p-6 rounded-xl shadow">
      <h1 className="text-xl font-bold mb-4 text-white">Регистрация</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="text"
          placeholder="Логин"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-2 rounded border border-gray-600 bg-transparent text-white"
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full p-2 rounded border border-gray-600 bg-transparent text-white"
          required
        />
        <div className="relative">
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-2 rounded border border-gray-600 bg-transparent text-white pr-20"
            required
          />
          <div className="absolute right-2 top-2 flex space-x-2">
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="px-2 py-1 bg-gray-700 text-xs rounded text-white"
            >
              {showPassword ? "Скрыть" : "Показать"}
            </button>
            <button
              type="button"
              onClick={copyPassword}
              className="px-2 py-1 bg-gray-700 text-xs rounded text-white"
            >
              Копировать
            </button>
          </div>
        </div>
        <div className="flex space-x-2">
          <button
            type="button"
            onClick={generatePassword}
            className="flex-1 py-2 bg-yellow-600 hover:bg-yellow-700 rounded text-white font-bold"
          >
            Сгенерировать пароль
          </button>
        </div>

        {error && <div className="text-red-400 text-sm">{JSON.stringify(error)}</div>}
        {message && <div className="text-green-400 text-sm">{message}</div>}

        <button
          type="submit"
          className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded text-white font-bold"
        >
          Зарегистрироваться
        </button>
      </form>
    </div>
  );
}
