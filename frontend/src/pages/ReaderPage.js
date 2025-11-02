/* Путь: frontend/src/pages/ReaderPage.js
   Назначение: Личный кабинет/избранное читателя. Совместимо с текущим Api.js.
   Важно:
   - Используем whoami() и tryGet() — НЕ требуется экспорт http из Api.js.
   - /api/accounts/dashboard/ и /api/news/favorites/ тянем через tryGet().
*/

import React from "react";
import css from "./ReaderPage.module.css";
import { whoami, tryGet } from "../Api";
import { Link, useLocation } from "react-router-dom";

function useAsync(asyncFn, deps = []) {
  const [state, setState] = React.useState({ loading: true, data: null, error: null });
  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await asyncFn();
        if (alive) setState({ loading: false, data, error: null });
      } catch (e) {
        if (alive) setState({ loading: false, data: null, error: e });
      }
    })();
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return state;
}

export default function ReaderPage() {
  const location = useLocation();

  const auth = useAsync(() => whoami(), []);
  const dash = useAsync(
    async () => (await tryGet("/accounts/dashboard/")) || {},
    [auth.data?.is_authenticated]
  );
  const favs = useAsync(
    async () => (await tryGet("/news/favorites/")) || [],
    [auth.data?.is_authenticated]
  );

  if (auth.loading) {
    return (
      <div className={css.wrap}>
        <h1 className={css.title}>Личный кабинет</h1>
        <div className={css.skeletonRow} />
        <div className={css.skeletonRow} />
      </div>
    );
  }

  if (!auth.data?.is_authenticated) {
    const next = encodeURIComponent(location.pathname + location.search);
    return (
      <div className={css.wrap}>
        <h1 className={css.title}>Личный кабинет</h1>
        <p className={css.muted}>Чтобы видеть избранное и статистику, войдите в аккаунт.</p>
        <div className={css.actions}>
          <Link className={css.btn} to={`/login?next=${next}`}>Войти</Link>
          <Link className={css.btnGhost} to="/register">Зарегистрироваться</Link>
        </div>
      </div>
    );
  }

  const user = auth.data?.user;
  const counters = dash?.data?.counters || {};
  const itemsRaw = Array.isArray(favs?.data?.results) ? favs.data.results : (favs?.data || []);
  const items = Array.isArray(itemsRaw) ? itemsRaw : [];

  return (
    <div className={css.wrap}>
      <nav className={css.breadcrumbs}>
        <Link to="/">Главная</Link>
        <span>›</span>
        <span>Личный кабинет</span>
      </nav>

      <h1 className={css.title}>Личный кабинет</h1>

      <section className={css.profileCard}>
        <div className={css.avatar} aria-hidden />
        <div className={css.profileInfo}>
          <div className={css.username}>{user?.first_name || user?.username || "Пользователь"}</div>
          {user?.email && <div className={css.email}>{user.email}</div>}
        </div>
      </section>

      <section className={css.tiles}>
        <div className={css.tile}>
          <div className={css.tileLabel}>Всего материалов</div>
          <div className={css.tileValue}>{counters.articles_total ?? 0}</div>
        </div>
        <div className={css.tile}>
          <div className={css.tileLabel}>Опубликовано</div>
          <div className={css.tileValue}>{counters.articles_published ?? 0}</div>
        </div>
        <div className={css.tile}>
          <div className={css.tileLabel}>Черновики</div>
          <div className={css.tileValue}>{counters.articles_draft ?? 0}</div>
        </div>
      </section>

      <section className={css.block}>
        <h2 className={css.h2}>Избранное</h2>
        {favs.loading && <div className={css.muted}>Загружаем…</div>}
        {!favs.loading && items.length === 0 && (
          <div className={css.muted}>Пока пусто. Нажимайте на сердечко на карточках новостей, чтобы добавить сюда.</div>
        )}
        <div className={css.grid}>
          {items.map((it) => {
            const slug = it?.slug || it?.seo_slug || it?.url_slug;
            return (
              <Link key={(it.id || slug)} to={slug ? `/news/${slug}/` : "#"} className={css.card}>
                <div className={css.cardTitle}>{it?.title || "Без заголовка"}</div>
                {it?.source_name && (
                  <div className={css.cardSource}>Источник: <span>{it.source_name}</span></div>
                )}
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
