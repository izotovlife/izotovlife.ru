# izotovlife.ru — бэкенд

Проект соответствует состоянию репозитория на коммит `47cc4a1` и включает защиту админ-панели через приложение `security`.

## Быстрый запуск (локальная разработка)

1. **Создай виртуальное окружение и установи зависимости**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Подготовь файл окружения**
   ```bash
   cp .env.example .env
   ```
   При необходимости дополни `.env` реальными значениями. По умолчанию включён режим `DEBUG` и используется SQLite.

3. **Выполни миграции и создай суперпользователя**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Запусти сервер разработки**
   ```bash
   python manage.py runserver
   ```

### Как работает защита админки

* При `DEBUG=True` доступ к `/admin/` открыт для упрощения разработки.
* В боевом режиме (`DEBUG=False`) требуется одноразовая ссылка из приложения `security` или подключение с IP из переменной `TRUSTED_ADMIN_IPS`.
* Одноразовые ссылки выдаются через POST `/api/security/admin-session-login/`.

## Настройка для PostgreSQL

Для продакшена заполни переменные `POSTGRES_*` в `.env`. Если они указаны, проект автоматически переключится на PostgreSQL.

## Полезные ссылки

* Админка: `/admin/`
* API защиты: `/api/security/`
* Документация по фронтенду находится в каталоге `frontend/`.
