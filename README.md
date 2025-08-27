# README.md
# Путь: README.md
# Назначение: общее описание проекта и пошаговая инструкция запуска для новичка.

## Описание
Проект **izotovlife.ru** — учебный новостной агрегатор на **Django + React** с базой данных **PostgreSQL**.  
Пользователи могут регистрироваться, заполнять профиль (фото, имя, фамилия, описание), публиковать новости.  
Каждая новость проходит модерацию редактором.  
Админка доступна только через одноразовую ссылку, сессия администратора живёт 10 минут бездействия.

Фронтенд использует **Materialize CSS**. Шаблонов Django (HTML) нет — весь интерфейс реализован в React.

## Установка (Windows 10 + PyCharm Community)
1. **Клонировать репозиторий**:
   ```bash
   git clone <ссылка-на-репо>
   cd izotovlife.ru
   ```
2. **Открыть папку `izotovlife.ru` в PyCharm Community Edition**.

### Backend (Django)
1. Создать виртуальное окружение (в терминале PyCharm):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
2. Установить зависимости:
   ```bash
   pip install django djangorestframework djangorestframework-simplejwt psycopg2-binary corsheaders
   ```
3. Настроить PostgreSQL (создать базу `izotovlife` и пользователя `Izotoff` с паролем `Jn4jnbeWllmhjds`).
4. Выполнить миграции и создать суперпользователя:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
5. Запустить сервер:
   ```bash
   python manage.py runserver
   ```

### Генерация ссылки в админку
```bash
python manage.py open_admin
```
Команда выведет одноразовый URL вида `/admin/<token>/`. Перейдите по нему, чтобы попасть в админку (`/_internal_admin/`).  
Сессия завершится через 10 минут бездействия.

### Frontend (React)
1. Установить зависимости:
   ```bash
   cd frontend
   npm install
   ```
2. Запустить дев-сервер React:
   ```bash
   npm start
   ```
Фронтенд доступен на `http://localhost:3000`, backend — на `http://127.0.0.1:8000`.

## Основные возможности
- Регистрация и авторизация (JWT).
- Редактирование профиля с фото и описанием.
- Добавление новостей авторами (идут на модерацию).
- Модерация и публикация редактором.
- Популярные новости и бесконечная лента.

Приятной работы!
