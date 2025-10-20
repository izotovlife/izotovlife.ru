// Путь: frontend/src/pages/LoginPage.js
// Назначение: Форма входа (JWT) + соц-логины через поп-ап.
// Что нового:
//  - Кнопка Google скрыта (feature-flag), VK и Яндекс работают через поп-ап и возвращают JWT.
//  - Для суперпользователя идём в админку через одноразовый admin_url.
//  - Для остальных используем redirect_url с бэка.
//  - Ничего лишнего не удалено. Добавлены обработчики handleVK/handleYandex и скрытие Google.

import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { setToken, login, whoami, adminSessionLogin, socialLoginPopup } from "../Api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      // 1) Логин по паролю → получаем JWT
      const res = await login(username, password);
      setToken(res.access);

      // 2) Кто вошёл?
      const meRes = await whoami();

      if (meRes?.is_superuser) {
        // 3) Суперпользователь → одноразовый вход в админку
        const sec = await adminSessionLogin();
        if (sec?.admin_url) {
          window.location.href = sec.admin_url;
        } else {
          setError("Не удалось получить ссылку для входа в админку.");
        }
      } else {
        // 4) Обычный пользователь → редирект
        if (meRes?.redirect_url) navigate(meRes.redirect_url);
        else navigate("/");
      }
    } catch (err) {
      console.error("Ошибка входа:", err);
      setError(
        err?.response?.data?.detail || err.message || "Ошибка входа. Попробуйте снова."
      );
    }
  };

  // Базовый URL бэкенда (для allauth)
  const backendUrl = (process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/+$/,'');

  // Фича-флаг: Google отключаем (по умолчанию скрыт)
  const ENABLE_GOOGLE = (process.env.REACT_APP_ENABLE_GOOGLE || "0") === "1";

  // --- Соц-логин через поп-ап: VK ---
  const handleVK = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await socialLoginPopup("vk");       // /accounts/vk/login/?next=/api/auth/social/complete/
      const meRes = await whoami();
      if (meRes?.is_superuser) {
        try {
          const sec = await adminSessionLogin();
          if (sec?.admin_url) { window.location.href = sec.admin_url; return; }
        } catch {}
        window.location.href = "/admin/";
      } else {
        if (meRes?.redirect_url) navigate(meRes.redirect_url);
        else navigate("/");
      }
    } catch (err) {
      console.error("VK auth error:", err);
      setError(err?.message || "Не удалось войти через VK.");
    }
  };

  // --- Соц-логин через поп-ап: Яндекс ---
  const handleYandex = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      await socialLoginPopup("yandex");   // /accounts/yandex/login/?next=/api/auth/social/complete/
      const meRes = await whoami();
      if (meRes?.is_superuser) {
        try {
          const sec = await adminSessionLogin();
          if (sec?.admin_url) { window.location.href = sec.admin_url; return; }
        } catch {}
        window.location.href = "/admin/";
      } else {
        if (meRes?.redirect_url) navigate(meRes.redirect_url);
        else navigate("/");
      }
    } catch (err) {
      console.error("Yandex auth error:", err);
      setError(err?.message || "Не удалось войти через Яндекс.");
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

      {/* Доп. ссылки */}
      <div className="mt-4 flex justify-between text-sm text-gray-300">
        <Link to="/register" className="hover:underline">Регистрация</Link>
        <Link to="/reset-password" className="hover:underline">Забыли пароль?</Link>
      </div>

      {/* Соц. кнопки */}
      <div className="mt-6">
        <p className="text-center text-gray-400 mb-2">или войдите через:</p>
        <div className="flex flex-col gap-2">
          {/* VK — поп-ап */}
          <a
            href={`${backendUrl}/accounts/vk/login/?process=login&next=/api/auth/social/complete/`}
            onClick={handleVK}
            className="w-full py-2 rounded text-white font-bold text-center bg-[#4a76a8] hover:opacity-90"
          >
            Войти через VK
          </a>

          {/* Яндекс — поп-ап */}
          <a
            href={`${backendUrl}/accounts/yandex/login/?process=login&next=/api/auth/social/complete/`}
            onClick={handleYandex}
            className="w-full py-2 rounded text-black font-bold text-center bg-[#ffcc00] hover:opacity-90"
          >
            Войти через Яндекс
          </a>

          {/* Google скрыт (можно включить через REACT_APP_ENABLE_GOOGLE=1) */}
          {ENABLE_GOOGLE && (
            <a
              href={`${backendUrl}/accounts/google/login/?process=login&next=/api/auth/social/complete/`}
              onClick={(e) => e.preventDefault()}
              className="w-full py-2 rounded text-white font-bold text-center bg-[#db4437] hover:opacity-90"
            >
              Войти через Google
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
