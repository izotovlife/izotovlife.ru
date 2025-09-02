// frontend/src/App.js
// Главный layout фронтенда: 3 колонки
// Слева — короткие новости, центр — популярное + лента, справа — погода, курсы валют, текстовые новости

import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

// Верхнее меню
import Navbar from "./components/Navbar";

// Центральные блоки
import NewsList from "./components/NewsList";
import Popular from "./components/Popular";
import NewsDetail from "./components/NewsDetail";
import Register from "./components/Register";
import Login from "./components/Login";
import Profile from "./components/Profile";
import AddNews from "./components/AddNews";
import Moderation from "./components/Moderation";


// Боковые блоки
import SidebarNews from "./components/SidebarNews";
import SidebarExtraNews from "./components/SidebarExtraNews";
import Weather from "./components/Weather";
import Currency from "./components/Currency";

// Новый компонент для категорий
import CategoryNews from "./components/CategoryNews";

function App() {
  return (
    <Router>
      <Navbar />
      <main className="bg-[var(--color-bg)] min-h-screen">
        <div className="layout">

          {/* Левая колонка — короткие новости */}
          <aside className="left-column">
            <SidebarNews />
          </aside>

          {/* Центральная колонка */}
          <section className="center-column">
            <Routes>
              {/* Главная */}
              <Route
                path="/"
                element={
                  <>
                    <Popular />
                    <h1 className="text-2xl font-bold mt-6 mb-4">Лента новостей</h1>
                    <NewsList />
                  </>
                }
              />

              {/* Новость в деталях */}
              <Route path="/news/:id" element={<NewsDetail />} />

              {/* Новости по категории */}
              <Route path="/category/:slug" element={<CategoryNews />} />

              {/* Популярное */}
              <Route path="/popular" element={<Popular />} />

              {/* Регистрация / Логин */}
              <Route path="/register" element={<Register />} />
              <Route path="/login" element={<Login />} />

              {/* Профиль */}
              <Route path="/profile" element={<Profile />} />

              {/* Добавление и модерация */}
              <Route path="/add" element={<AddNews />} />
              <Route path="/moderation" element={<Moderation />} />
            </Routes>
          </section>

          {/* Правая колонка */}
          <aside className="right-column">
            <Weather />
            <Currency />
            <SidebarExtraNews />
          </aside>
        </div>
      </main>
    </Router>
  );
}

export default App;
