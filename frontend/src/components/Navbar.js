// ===== ФАЙЛ: frontend/src/components/Navbar.js =====
// ПУТЬ: C:\\Users\\ASUS Vivobook\\PycharmProjects\\izotovlife\\frontend\\src\\components\\Navbar.js
// НАЗНАЧЕНИЕ: Верхняя панель навигации сайта.
// ОПИСАНИЕ: Использует Materialize CSS для привлекательного дизайна и
//            показывает ссылки в зависимости от статуса авторизации.

import React from "react";
import { Link, useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    navigate("/login");
  };

  const isLoggedIn = !!localStorage.getItem("access");

  return (
    <nav className="teal lighten-1">
      <div className="nav-wrapper container">
        <Link to="/" className="brand-logo">IzotovLife</Link>
        <ul id="nav-mobile" className="right hide-on-med-and-down">
          <li><Link to="/register">Регистрация</Link></li>
          {isLoggedIn ? (
            <>
              <li><Link to="/profile">Профиль</Link></li>
              <li>
                <button
                  onClick={handleLogout}
                  className="btn waves-effect waves-light teal darken-2"
                >
                  Выход
                </button>
              </li>
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
