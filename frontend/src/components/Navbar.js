// frontend/src/components/Navbar.js
// Путь: frontend/src/components/Navbar.js
// Назначение: верхняя навигационная панель сайта.

import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../api";

function Navbar() {
  const navigate = useNavigate();
  const [isStaff, setIsStaff] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    navigate("/login");
  };

  const isLoggedIn = !!localStorage.getItem("access");

  useEffect(() => {
    async function fetchProfile() {
      try {
        const res = await api.get("accounts/profile/");
        setIsStaff(res.data.is_staff);
      } catch {
        setIsStaff(false);
      }
    }
    if (isLoggedIn) {
      fetchProfile();
    }
  }, [isLoggedIn]);

  return (
    <nav className="navbar">
      <div className="nav-wrapper">
        <Link to="/" className="brand-logo">IzotovLife</Link>
        <ul id="nav-mobile" className="right hide-on-med-and-down">
          <li><Link to="/register">Регистрация</Link></li>
          {isLoggedIn ? (
            <>
              <li><Link to="/add">Добавить новость</Link></li>
              {isStaff && <li><Link to="/moderation">Модерация</Link></li>}
              <li><Link to="/favorites">Избранное</Link></li>
              <li><Link to="/profile">Профиль</Link></li>
              <li><button onClick={handleLogout} className="btn-flat">Выход</button></li>
            </>
          ) : (
            <li><Link to="/login">Вход</Link></li>
          )}
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
