// frontend/src/components/TopNews.js
// Компонент вывода топовых новостей по периодам

import React, { useState, useEffect, useCallback } from "react";
import api from "../api";

function TopNews() {
  const [period, setPeriod] = useState("day");
  const [items, setItems] = useState([]);

  const loadTop = useCallback(async () => {
    try {
      const res = await api.get("news/top/", { params: { period } });
      setItems(res.data);
    } catch (err) {
      console.error("Ошибка загрузки топ-новостей:", err);
    }
  }, [period]);

  useEffect(() => {
    loadTop();
  }, [loadTop]);

  return (
    <div className="container">
      <h4>Топ</h4>
      <div className="row">
        <div className="col s12">
          <button
            className={`btn ${period === "day" ? "" : "grey lighten-1"}`}
            onClick={() => setPeriod("day")}
          >
            День
          </button>
          <button
            className={`btn ${period === "week" ? "" : "grey lighten-1"}`}
            onClick={() => setPeriod("week")}
            style={{ marginLeft: "10px" }}
          >
            Неделя
          </button>
        </div>
      </div>
      <div className="row">
        {items.map((n, index) => (
          <div key={`${n.id}-${index}`} className="col s12 m6 l4">
            <div className="card">
              {n.image && (
                <div className="card-image">
                  <img src={n.image} alt={n.title} />
                </div>
              )}
              <div className="card-content">
                <span className="card-title">
                  <a href={n.link} target="_blank" rel="noopener noreferrer">
                    {n.title}
                  </a>
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default TopNews;
