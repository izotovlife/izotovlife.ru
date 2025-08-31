// frontend/static/js/admin-login.js
// Назначение: авторизация суперпользователя и редирект в админку по одноразовой ссылке
// С учётом TTL ссылки

async function loginAndRedirect(username, password) {
  try {
    // 1. JWT логин
    let resp = await fetch("http://127.0.0.1:8000/api/token/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    let tokens = await resp.json();

    if (!resp.ok) throw new Error("Ошибка входа");

    // 2. Получаем профиль
    resp = await fetch("http://127.0.0.1:8000/api/accounts/profile/", {
      headers: { "Authorization": `Bearer ${tokens.access}` }
    });
    let profile = await resp.json();

    if (!profile.is_superuser) {
      alert("У вас нет доступа в админку");
      return;
    }

    // 3. Генерация одноразовой ссылки
    resp = await fetch("http://127.0.0.1:8000/api/accounts/superuser-admin-link/", {
      method: "POST",
      headers: { "Authorization": `Bearer ${tokens.access}` }
    });
    let data = await resp.json();

    if (!resp.ok) throw new Error("Не удалось получить админ-ссылку");

    // 4. Проверка TTL
    const expiresIn = data.expires_in || 0;
    if (expiresIn <= 0) {
      alert("Срок действия ссылки истёк, попробуйте снова");
      return;
    }

    // 5. Редирект в админку
    window.location.href = data.url;

  } catch (err) {
    console.error(err);
    alert("Ошибка входа");
  }
}
