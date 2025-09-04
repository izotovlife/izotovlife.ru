import { useEffect, useState, useCallback } from "react";
import { useLocation, Link, useNavigate } from "react-router-dom";
import axios from "axios";

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

export default function SearchPage() {
  const queryParams = useQuery();
  const navigate = useNavigate();

  const initialQuery = queryParams.get("q") || "";
  const initialCategory = queryParams.get("category") || "";

  const [query, setQuery] = useState(initialQuery);
  const [category, setCategory] = useState(initialCategory);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [nextPage, setNextPage] = useState(null);
  const [categories, setCategories] = useState([]);

  // Загружаем список категорий
  useEffect(() => {
    async function fetchCategories() {
      try {
        const res = await axios.get("/api/news/categories/");
        setCategories(res.data);
      } catch (err) {
        console.error("Ошибка загрузки категорий:", err);
      }
    }
    fetchCategories();
  }, []);

  // Функция загрузки данных с API поиска
  const fetchData = useCallback(
    async (url, reset = false) => {
      if (!query && !category) return;
      setLoading(true);
      try {
        const res = await axios.get(url);
        const data = res.data;
        setResults((prev) =>
          reset ? data.results || data : [...prev, ...(data.results || data)]
        );
        setNextPage(data.next);
      } catch (err) {
        console.error("Ошибка поиска:", err);
      } finally {
        setLoading(false);
      }
    },
    [query, category]
  );

  // При изменении query/category → новый поиск
  useEffect(() => {
    if (!query && !category) {
      setResults([]);
      return;
    }
    const params = new URLSearchParams();
    if (query) params.append("q", query);
    if (category) params.append("category", category);

    const url = `/api/news/search/?${params.toString()}`;

    setResults([]);
    setNextPage(null);
    fetchData(url, true);

    // синхронизируем URL в браузере
    navigate(`/search?${params.toString()}`, { replace: true });
  }, [query, category, fetchData, navigate]);

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-4">Поиск по сайту</h1>

      {/* Поле поиска + фильтр по категории */}
      <div className="flex gap-3 mb-6">
        <input
          type="text"
          value={query}
          placeholder="Введите запрос..."
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Все категории</option>
          {categories.map((c) => (
            <option key={c.id} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {/* Состояния */}
      {loading && results.length === 0 && <p>Загрузка...</p>}

      {!loading && results.length === 0 && (query || category) && (
        <p>Ничего не найдено.</p>
      )}

      {/* Список новостей */}
      <ul className="space-y-4">
        {results.map((news) => (
          <li key={news.id} className="border-b pb-2">
            <Link
              to={`/news/${news.id}`}
              className="text-lg font-semibold text-blue-600 hover:underline"
            >
              {news.title}
            </Link>
            <p className="text-gray-600 text-sm">
              {news.category?.name} •{" "}
              {new Date(news.created_at).toLocaleString()}
            </p>
          </li>
        ))}
      </ul>

      {/* Кнопка пагинации */}
      {nextPage && (
        <div className="mt-4">
          <button
            onClick={() => fetchData(nextPage)}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Загрузка..." : "Загрузить ещё"}
          </button>
        </div>
      )}
    </div>
  );
}
