// frontend/src/components/Register.js
// Путь: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\frontend\src\components\Register.js
// Назначение: форма регистрации новых авторов.
// Исправлено: обработка формы через useCallback, добавлены зависимости в useEffect (если нужны), улучшен UX.

import React, { useState, useCallback } from "react";
import api from "../api";

function Register() {
  const [formData, setFormData] = useState({
    username: "",
    password: "",
    first_name: "",
    last_name: "",
    description: "",
  });

  const [message, setMessage] = useState("");

  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  }, []);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      try {
        await api.post("accounts/register/", formData);
        setMessage("Регистрация успешна! Теперь вы можете войти.");
        setFormData({
          username: "",
          password: "",
          first_name: "",
          last_name: "",
          description: "",
        });
      } catch (err) {
        console.error("Ошибка регистрации:", err);
        setMessage("Ошибка при регистрации. Попробуйте ещё раз.");
      }
    },
    [formData]
  );

  return (
    <div className="container">
      <h4>Регистрация автора</h4>
      <form onSubmit={handleSubmit}>
        <div className="input-field">
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
          />
          <label htmlFor="username" className={formData.username ? "active" : ""}>
            Имя пользователя
          </label>
        </div>

        <div className="input-field">
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
          />
          <label htmlFor="password" className={formData.password ? "active" : ""}>
            Пароль
          </label>
        </div>

        <div className="input-field">
          <input
            type="text"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
          />
          <label htmlFor="first_name" className={formData.first_name ? "active" : ""}>
            Имя
          </label>
        </div>

        <div className="input-field">
          <input
            type="text"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
          />
          <label htmlFor="last_name" className={formData.last_name ? "active" : ""}>
            Фамилия
          </label>
        </div>

        <div className="input-field">
          <textarea
            className="materialize-textarea"
            name="description"
            value={formData.description}
            onChange={handleChange}
          ></textarea>
          <label htmlFor="description" className={formData.description ? "active" : ""}>
            О себе
          </label>
        </div>

        <button className="btn waves-effect waves-light" type="submit">
          Зарегистрироваться
        </button>
      </form>

      {message && <p className="green-text">{message}</p>}
    </div>
  );
}

export default Register;
