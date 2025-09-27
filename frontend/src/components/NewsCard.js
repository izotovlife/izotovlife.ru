// frontend/src/components/NewsCard.js
import React from "react";
import { Link } from "react-router-dom";
import { getImageUrl } from "../utils/getImageUrl"; // ✅ правильный импорт

export default function NewsCard({ item }) {
  const type = item.type || "rss";
  const internalUrl = `/${type}/${item.slug || item.id}`;

  const imageSrc = getImageUrl(item.image);

  return (
    <div className="bg-[#0b132b] rounded-lg overflow-hidden shadow hover:shadow-lg transition flex flex-col">
      <div className="w-full aspect-[16/9] overflow-hidden flex items-center justify-center bg-black">
        <img
          src={imageSrc}
          alt={item.title}
          loading="lazy"
          className="w-full h-full object-cover"
          onError={(e) => {
            e.currentTarget.onerror = null;
            e.currentTarget.src = getImageUrl(null);
          }}
        />
      </div>

      <div className="p-3 flex flex-col flex-grow">
        <h3 className="text-lg font-semibold text-yellow-400 mb-2">
          <Link to={internalUrl} className="hover:underline">
            {item.title}
          </Link>
        </h3>

        <div className="mt-auto">
          <Link to={internalUrl} className="text-blue-400 hover:underline">
            Подробнее →
          </Link>
        </div>
      </div>
    </div>
  );
}
