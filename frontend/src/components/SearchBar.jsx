//izotovlife.ru\frontend\src\components\SearchBar.jsx

import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

export default function SearchBar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const navigate = useNavigate();

  const handleSearch = async () => {
    if (!query.trim()) return;
    try {
      const res = await axios.get(
        `/api/news/search/?q=${encodeURIComponent(query)}`
      );
      setResults(res.data.results || res.data);
    } catch (err) {
      console.error("Ошибка поиска:", err);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div style={{ position: "relative" }}>
      <input
        type="text"
        placeholder="Поиск по сайту..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button onClick={handleSearch}>🔍</button>

      {results.length > 0 && (
        <ul
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            background: "white",
            border: "1px solid #ccc",
            zIndex: 1000,
          }}
        >
          {results.map((n) => (
            <li key={n.id}>
              <a
                href={`/news/${n.id}`}
                onClick={(e) => {
                  e.preventDefault();
                  navigate(`/news/${n.id}`);
                  setResults([]);
                  setQuery("");
                }}
              >
                {n.title}
              </a>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
