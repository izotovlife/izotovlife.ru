// frontend/src/components/NewsCard.js
// Назначение: Универсальная карточка новости — выбирает вариант отображения (с картинкой или текстовую).
// Путь: frontend/src/components/NewsCard.js

import React from "react";
import NewsCardImage from "./NewsCardImage";
import NewsCardText from "./NewsCardText";

export default function NewsCard({ item }) {
  if (!item) return null;

  // Если есть изображение → показываем карточку с картинкой
  if (item.image) {
    return <NewsCardImage item={item} />;
  }

  // Иначе показываем текстовую карточку
  return <NewsCardText item={item} />;
}
