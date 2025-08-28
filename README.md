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

## 2. Вход в админку
Администратор и авторы используют одну форму входа.

1. Отправьте `POST /api/accounts/login/` с полями `username` и `password`.
2. Если учётные данные принадлежат суперпользователю, сервер вернёт:
   ```json
   {"admin_url": "/admin/AbCdEf.../", "expires_in": 600}
   ```
   Перейдите по `admin_url` — это одноразовый адрес админки.
3. Для обычного пользователя ответ содержит `access` и `refresh` токены.
4. Сессия в админке действует 10 минут без активности. Для выхода отправьте `POST /admin/logout/`.

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
- В верхней части страницы расположена строка поиска и вкладки категорий на Materialize CSS.
- Вкладки позволяют быстро переключаться между разделами новостей.
- Поддерживается «лнивая» подгрузка: при прокрутке вниз автоматически запрашивается следующая страница.
- В навигации отображается логотип проекта (`frontend/src/logo.svg`), а вкладка браузера использует кастомную иконку `frontend/public/favicon.svg`.

## 6. JWT-аутентификация
- Получение токена: `POST /api/accounts/login/` (суперпользователь получает ссылку в админку).
- Обновление токена: `POST /api/token/refresh/`.
