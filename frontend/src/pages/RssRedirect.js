// frontend/src/pages/RssRedirect.js
// Назначение: Легаси-редирект со старого пути /rss/:id на актуальный /news/imported/:id.
// Поведение: сразу делает replace-навигацию, чтобы в истории не оставалась промежуточная страница.
// Путь: frontend/src/pages/RssRedirect.js

import React, { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function RssRedirect() {
  const { id } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    const numericId = String(id || "").trim();
    if (numericId) {
      navigate(`/news/imported/${numericId}`, { replace: true });
    } else {
      navigate(`/`, { replace: true });
    }
  }, [id, navigate]);

  return (
    <div className="container mx-auto px-4 py-6" style={{ color: "var(--muted,#ccc)" }}>
      Перенаправляем…
    </div>
  );
}
