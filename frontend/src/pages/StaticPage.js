// frontend/src/pages/StaticPage.js
// Назначение: Вывод содержимого статической страницы (Политика, О компании и т.д.)
// Путь: frontend/src/pages/StaticPage.js

import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchPage } from "../Api";
import styles from "./StaticPage.module.css";

export default function StaticPage() {
  const { slug } = useParams();
  const [page, setPage] = useState(null);

  useEffect(() => {
    fetchPage(slug).then(setPage).catch(console.error);
  }, [slug]);

  if (!page) {
    return <div className="text-gray-400">Загрузка...</div>;
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>{page.title}</h1>
      <div
        className={`prose ${styles.prose}`}
        dangerouslySetInnerHTML={{ __html: page.content }}
      />
    </div>
  );
}
