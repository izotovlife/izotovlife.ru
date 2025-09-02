import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FiMenu, FiSearch, FiArrowRight } from "react-icons/fi";
import logo from "../assets/logo.png";

function Navbar() {
  const [categories, setCategories] = useState([]);
  const [openMenu, setOpenMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [showSearch, setShowSearch] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setCategories([
      { id: 1, name: "Политика", slug: "politics" },
      { id: 2, name: "Экономика", slug: "economy" },
      { id: 3, name: "Спорт", slug: "sport" },
      { id: 4, name: "Технологии", slug: "technology" },
      { id: 5, name: "Культура", slug: "culture" },
      { id: 6, name: "Лента новостей", slug: "news-feed" },
      { id: 7, name: "Общество", slug: "society" },
    ]);
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim() !== "") {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchQuery("");
      setShowSearch(false);
    }
  };

  return (
    <header className="w-full shadow-md sticky top-0 z-50 bg-blue-600">
      <nav className="main-navbar max-w-7xl mx-auto">
        {/* Логотип */}
        <Link to="/" className="flex items-center h-full pr-6">
          <img src={logo} alt="Логотип" className="h-10 object-contain" />
        </Link>

        {/* Категории (desktop) */}
        <div className="hidden lg:flex nav-links">
          {categories.map((cat) => (
            <Link
              key={cat.id}
              to={`/category/${cat.slug}`}
              className="hover:text-yellow-300 transition whitespace-nowrap"
            >
              {cat.name}
            </Link>
          ))}
        </div>

        {/* Блок справа: поиск и меню */}
        <div className="nav-right flex items-center gap-2 relative">
          {showSearch ? (
            <form onSubmit={handleSearch} className="flex items-center">
              <input
                type="text"
                placeholder="Поиск..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-40 px-2 py-1 rounded-l-md text-black outline-none"
                autoFocus
              />
              <button
                type="submit"
                className="px-2 py-1 bg-blue-700 text-white rounded-r-md"
              >
                <FiArrowRight />
              </button>
            </form>
          ) : (
            <button
              aria-label="Поиск"
              onClick={() => {
                setShowSearch(true);
                setOpenMenu(false);
              }}
              className="p-1 hover:text-yellow-300 transition"
            >
              <FiSearch size={22} />
            </button>
          )}
          <div className="relative">
            <button
              aria-label="Меню"
              onClick={() => {
                setOpenMenu((prev) => !prev);
                setShowSearch(false);
              }}
              className="p-1 hover:text-yellow-300 transition"
            >
              <FiMenu size={24} />
            </button>
            {openMenu && (
              <div className="absolute right-0 mt-2 w-40 bg-white shadow-lg rounded-md z-50 flex flex-col">
                <Link
                  to="/login"
                  className="px-4 py-2 text-gray-700 hover:text-blue-600 transition"
                  onClick={() => setOpenMenu(false)}
                >
                  Вход
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-gray-700 hover:text-blue-600 transition"
                  onClick={() => setOpenMenu(false)}
                >
                  Регистрация
                </Link>
              </div>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
}

export default Navbar;
