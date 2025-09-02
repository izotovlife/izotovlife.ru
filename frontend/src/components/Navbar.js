import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FiMenu, FiX, FiSearch, FiArrowRight } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
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

        {/* Блок справа (поиск + меню, единственный) */}
        <div className="nav-right">
          {/* Desktop */}
          <div className="hidden lg:flex items-center space-x-4">
            <button
              aria-label="Поиск"
              onClick={() => setShowSearch(!showSearch)}
              className="p-1 hover:text-yellow-300 transition"
            >
              <FiSearch size={22} />
            </button>
            <button
              aria-label="Меню"
              onClick={() => setOpenMenu(true)}
              className="p-1 hover:text-yellow-300 transition"
            >
              <FiMenu size={24} />
            </button>
          </div>

          {/* Mobile */}
          <div className="flex lg:hidden items-center space-x-4">
            <button
              aria-label="Поиск"
              onClick={() => setShowSearch(!showSearch)}
              className="p-1 hover:text-yellow-300 transition"
            >
              <FiSearch size={20} />
            </button>
            <button
              aria-label="Меню"
              onClick={() => setOpenMenu(true)}
              className="p-1 hover:text-yellow-300 transition"
            >
              <FiMenu size={22} />
            </button>
          </div>
        </div>
      </nav>

      {/* Поиск (overlay под шапкой) */}
      <AnimatePresence>
        {showSearch && (
          <motion.div
            initial={{ y: -40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -40, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute left-0 right-0 top-16 bg-white shadow-md z-40 px-4 py-3"
          >
            <form onSubmit={handleSearch} className="flex items-center">
              <input
                type="text"
                placeholder="Поиск..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-grow px-3 py-2 border rounded-l-md outline-none text-black"
                autoFocus
              />
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-r-md hover:bg-blue-700"
              >
                <FiArrowRight />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Drawer меню */}
      <AnimatePresence>
        {openMenu && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="fixed inset-0 bg-black z-40"
              onClick={() => setOpenMenu(false)}
            />

            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "tween", duration: 0.3 }}
              className="fixed top-0 right-0 h-full w-64 bg-white shadow-xl z-50 p-6 flex flex-col"
            >
              <div className="flex justify-between items-center mb-6 border-b pb-3">
                <span className="text-lg font-bold text-blue-600">Меню</span>
                <button
                  aria-label="Закрыть меню"
                  onClick={() => setOpenMenu(false)}
                  className="text-gray-600 hover:text-black"
                >
                  <FiX size={24} />
                </button>
              </div>

              <div className="flex flex-col space-y-4 mb-6">
                {categories.map((cat) => (
                  <Link
                    key={cat.id}
                    to={`/category/${cat.slug}`}
                    className="text-gray-800 font-medium hover:text-blue-600 transition"
                    onClick={() => setOpenMenu(false)}
                  >
                    {cat.name}
                  </Link>
                ))}
              </div>

              <hr className="my-4" />

              <div className="flex flex-col space-y-3">
                <Link
                  to="/login"
                  className="text-gray-700 hover:text-blue-600 transition"
                  onClick={() => setOpenMenu(false)}
                >
                  Вход
                </Link>
                <Link
                  to="/register"
                  className="text-gray-700 hover:text-blue-600 transition"
                  onClick={() => setOpenMenu(false)}
                >
                  Регистрация
                </Link>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </header>
  );
}

export default Navbar;
