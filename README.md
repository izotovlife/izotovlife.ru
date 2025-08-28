# ===== ФАЙЛ: README.md =====
# ПУТЬ: C:\Users\ASUS Vivobook\PycharmProjects\izotovlife\README.md
# НАЗНАЧЕНИЕ: Общее описание проекта izotovlife.ru и инструкции для новичка.
# ОПИСАНИЕ: Пошаговая настройка Django + React приложения новостного агрегатора.

## 1. Подготовка окружения (Windows 10, PyCharm Community)
- Установите [Python 3.11](https://www.python.org/downloads/) и Git.
- Установите PostgreSQL и создайте базу `izotovlife` и пользователя `Izotoff` с паролем `Jn4jnbeWllmhjds`.
- Клонируйте репозиторий и откройте папку `backend` в PyCharm.
- Создайте виртуальное окружение и установите зависимости:
  ```bash
  pip install django djangorestframework django-cors-headers djangorestframework-simplejwt pillow feedparser
  ```
- Примените миграции:
  ```bash
  python manage.py migrate
  ```
- Создайте суперпользователя:
  ```bash
  python manage.py createsuperuser
  ```

## 2. Запуск админки
- Запросите одноразовую ссылку, указав логин и пароль суперпользователя:
  ```bash
  curl -X POST http://127.0.0.1:8000/admin/login/ \
       -H "Content-Type: application/json" \
       -d '{"username":"<ваш_логин>","password":"<ваш_пароль>"}'
  ```
- В ответ получите JSON с полем `url`, например `/admin/AbCdEf.../`.
- Перейдите по выданному адресу в браузере — вы попадёте в `/_internal_admin/`.
- Для выхода отправьте POST-запрос на `/admin/logout/`:
  ```bash
  curl -X POST http://127.0.0.1:8000/admin/logout/
  ```

## 3. Запуск серверов
- Backend:
  ```bash
  python manage.py runserver
  ```
- Frontend:
  ```bash
  cd frontend
  npm install
  npm start
  ```
  React-приложение использует Materialize CSS.

## 4. Работа с новостями
- Регистрация авторов: `POST /api/accounts/register/`.
- Создание новости автором: `POST /api/news/create/` (требуется JWT-токен).
- Просмотр своих новостей: `GET /api/news/mine/`.
- Редакторы проверяют неопубликованные новости: `GET /api/news/pending/` и подтверждают `POST /api/news/<id>/approve/`.
- Импорт новостей из RSS: `python manage.py fetch_rss` или кнопка «Запустить парсер RSS» в админке.
- Запустить парсер можно также запросом `POST /api/news/fetch/` (только для администратора).

## 5. Фронтенд
- Лента новостей на React показывает карточки с заголовком, изображением и ссылкой на первоисточник.
- Поиск и фильтр по категориям находятся в верхней части ленты.
- Поддерживается «ленивая» подгрузка: при прокрутке вниз подгружается следующая страница.

## 6. JWT-аутентификация
- Получение токена: `POST /api/token/` с полями `username` и `password`.
- Обновление токена: `POST /api/token/refresh/`.
