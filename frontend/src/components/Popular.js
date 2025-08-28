import React, { useEffect, useState, useCallback } from "react";
import api from "../api";
import { generateShareLink } from "../utils/share";

function Popular() {
  const [popular, setPopular] = useState([]);

  const loadPopular = useCallback(async () => {
    try {
      const res = await api.get("news/popular/");
      setPopular(res.data);
    } catch (err) {
      console.error("Ошибка загрузки популярных новостей:", err);
    }
  }, []);

  useEffect(() => {
    loadPopular();
  }, [loadPopular]);

  return (
    <div className="container">
      <h4>Популярное</h4>
      <div className="row">
        {popular.map((n) => (
          <div key={n.id} className="col s12 m6 l4">
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
              <div className="card-action">
                <a
                  href={generateShareLink("vk", n.link, n.title)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  VK
                </a>
                <a
                  href={generateShareLink("telegram", n.link, n.title)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Telegram
                </a>
                <a
                  href={generateShareLink("twitter", n.link, n.title)}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Twitter
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Popular;
