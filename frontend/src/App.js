// frontend/src/App.js
import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import NewsList from "./components/NewsList";
import Popular from "./components/Popular";
import Register from "./components/Register";
import Login from "./components/Login";
import Profile from "./components/Profile";  // ✅ добавили

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        {/* Главная страница сразу показывает "Популярное" и "Все новости" */}
        <Route path="/" element={<><Popular /><NewsList /></>} />

        {/* Страницы регистрации и логина */}
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />

        {/* Отдельная страница для популярного (по желанию) */}
        <Route path="/popular" element={<Popular />} />

        {/* ✅ Новый маршрут для профиля */}
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Router>
  );
}

export default App;
