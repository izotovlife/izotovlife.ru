// frontend/src/App.js
import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import NewsList from "./components/NewsList";
import Popular from "./components/Popular";
import Register from "./components/Register";
import Login from "./components/Login";
import Profile from "./components/Profile";
import AddNews from "./components/AddNews";
import Moderation from "./components/Moderation";
import Favorites from "./components/Favorites";

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

        {/* Маршруты профиля и работы с новостями */}
        <Route path="/profile" element={<Profile />} />
        <Route path="/add" element={<AddNews />} />
        <Route path="/moderation" element={<Moderation />} />
        <Route path="/favorites" element={<Favorites />} />
      </Routes>
    </Router>
  );
}

export default App;
