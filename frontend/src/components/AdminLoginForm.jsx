// frontend/components/AdminLoginForm.jsx
// Назначение: форма входа суперпользователя с генерацией одноразовой ссылки в админку
// Особенности:
//  - Таймер обратного отсчёта (TTL ссылки)
//  - По истечении времени редирект НЕ выполняется
//  - Отображается кнопка «Сгенерировать новую ссылку»

import { useState, useEffect } from "react";

export default function AdminLoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [countdown, setCountdown] = useState(null);
  const [adminUrl, setAdminUrl] = useState(null);
  const [tokens, setTokens] = useState(null);

  async function handleLogin(e) {
    e.preventDefault();

    try {
      // 1. JWT логин
      let resp = await fetch("http://127.0.0.1:8000/api/token/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      let data = await resp.json();
      if (!resp.ok) throw new Error("Ошибка входа");
      setTokens(data);

      // 2. Профиль
      resp = await fetch("http://127.0.0.1:8000/api/accounts/profile/", {
        headers: { "Authorization": `Bearer ${data.access}` }
      });
      let profile = await resp.json();

      if (!profile.is_superuser) {
        alert("Нет доступа в админку");
        return;
      }

      // 3. Генерация ссылки
      await generateLink(data.access);

    } catch (err) {
      console.error(err);
      alert("Ошибка авторизации");
    }
  }

  async function generateLink(accessToken) {
    try {
      const resp = await fetch("http://127.0.0.1:8000/api/accounts/superuser-admin-link/", {
        method: "POST",
        headers: { "Authorization": `Bearer ${accessToken}` }
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error("Ошибка генерации ссылки");

      setAdminUrl(data.url);
      setCountdown(data.expires_in || 0);
    } catch (err) {
      console.error(err);
      alert("Ошибка генерации ссылки");
    }
  }

  // Таймер обратного отсчёта
  useEffect(() => {
    if (countdown === null) return;
    if (countdown <= 0) return;

    const interval = setInterval(() => {
      setCountdown(prev => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(interval);
  }, [countdown]);

  return (
    <form onSubmit={handleLogin}>
      <input
        value={username}
        onChange={e => setUsername(e.target.value)}
        placeholder="Логин"
      />
      <input
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        placeholder="Пароль"
      />
      <button type="submit">Войти</button>

      {adminUrl && countdown > 0 && (
        <div style={{ marginTop: "15px" }}>
          <a href={adminUrl} target="_blank" rel="noopener noreferrer">
            🚀 Перейти в админку
          </a>
          <p style={{ color: "red" }}>
            ⏳ Ссылка истечёт через{" "}
            {Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, "0")}
          </p>
        </div>
      )}

      {adminUrl && countdown === 0 && (
        <div style={{ marginTop: "15px" }}>
          <p style={{ color: "red" }}>⚠️ Ссылка истекла</p>
          <button
            type="button"
            onClick={() => generateLink(tokens.access)}
          >
            🔄 Сгенерировать новую ссылку
          </button>
        </div>
      )}
    </form>
  );
}
