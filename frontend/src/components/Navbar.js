// frontend/src/components/Navbar.js
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
    <nav className="navbar">
      <div className="nav-wrapper">
        <Link to="/" className="brand-logo">IzotovLife</Link>
        <ul id="nav-mobile" className="right hide-on-med-and-down">
          <li><Link to="/register">Регистрация</Link></li>
          {isLoggedIn ? (
            <>
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
