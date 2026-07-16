# VK Kanban

Kanban-доска для учебной практики и защиты проекта. Приложение состоит из FastAPI backend и Flet frontend. Реализованы JWT-авторизация, ролевой доступ к доскам, карточки с drag-and-drop, комментарии, метки, приоритеты, фильтры, дедлайны и скрипты наполнения демо-данными.

## Стек

- Python 3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- SQLite по умолчанию
- Flet 0.85.3
- Docker Compose
- Pytest

## Структура проекта

```text
Kanban_VK/
  backend/
    app/
      api/          зависимости FastAPI
      core/         конфигурация, хэширование паролей, JWT
      db/           SQLAlchemy engine/session
      models/       ORM-модели
      routers/      API-роутеры
      schemas/      Pydantic-схемы
      services/     права, порядок карточек, фильтры, метки
    alembic/        миграции базы данных
    scripts/        seed- и smoke-скрипты
    tests/          backend-тесты
  frontend/
    app/
      components/   переиспользуемые Flet-компоненты
      views/        вход, список досок, доска, диалоги
      api_client.py HTTP-клиент к backend API
      drag_drop.py  расчет позиции при drop
      main.py       точка входа frontend
    tests/          frontend-тесты
  docker-compose.yml
  requirements.txt
```

## Возможности

MVP:

- Регистрация и вход по `login + password`.
- JWT Bearer token для защищенных API-запросов.
- Пароли хранятся в виде bcrypt-хэшей.
- Доски с владельцем и участниками.
- Роли: `owner`, `editor`, `viewer`.
- CRUD досок и список доступных досок.
- CRUD колонок.
- CRUD карточек.
- Редактирование `title` и `description` карточки.
- Перемещение карточек drag-and-drop между колонками и внутри колонки.
- Сохранение порядка карточек через поле `position`.
- Исполнитель и дедлайн карточки.
- Комментарии к карточкам.
- CRUD ролей участников.

Дополнительные функции:

- Метки/теги с заранее заданными цветами.
- Приоритеты карточек: low, medium, high, critical.
- Фильтры по тексту, приоритету, метке и просрочке.
- Баннер просроченных карточек.
- Шаблоны создания досок: пустая, фичи, отклики на вакансии.
- Фоновое обновление доски для простой демонстрации двух сессий.
- Docker Compose с отдельными сервисами backend и frontend.
- Скрипт наполнения моковыми данными для презентации.

## Локальная установка

Виртуальное окружение держим в корне проекта.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Переменные окружения

Backend использует префикс `KANBAN_`.

| Переменная | Значение по умолчанию | Назначение |
| --- | --- | --- |
| `KANBAN_DATABASE_URL` | `sqlite:///backend/kanban.db` | URL подключения SQLAlchemy |
| `KANBAN_SECRET_KEY` | `change-me-in-production` | Секрет для подписи JWT-токенов |
| `KANBAN_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Время жизни JWT в минутах |
| `KANBAN_API_PREFIX` | `/api` | Префикс API-роутов |

Frontend:

| Переменная | Значение по умолчанию | Назначение |
| --- | --- | --- |
| `KANBAN_API_BASE_URL` | `http://127.0.0.1:8000/api` | URL backend API |
| `KANBAN_FLET_HOST` | не задано | Host для Flet |
| `KANBAN_FLET_PORT` | `0` | Порт Flet; `0` означает автоматический выбор |
| `KANBAN_FLET_VIEW` | `flet_app` | Режим запуска Flet |

Для локальной настройки backend можно создать `backend/.env`:

```env
KANBAN_DATABASE_URL=sqlite:///./kanban.db
KANBAN_SECRET_KEY=replace-with-a-long-random-string
KANBAN_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

`KANBAN_SECRET_KEY` используется для подписи JWT-токенов. В реальном деплое его нельзя хранить в git.

## Локальный запуск

Запуск backend из папки `backend`:

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Адреса backend:

- API: `http://127.0.0.1:8000/api`
- Swagger: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

Запуск frontend из корня проекта во втором терминале:

```powershell
.\.venv\Scripts\Activate.ps1
python -m frontend.app.main
```

## Запуск через Docker Compose

```powershell
docker compose up --build
```

Адреса Docker-запуска:

- Backend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Frontend: `http://127.0.0.1:8550`

Compose поднимает два сервиса:

- `backend`: FastAPI-приложение на порту `8000`.
- `frontend`: Flet web-приложение на порту `8550`.

Для SQLite в Docker используется постоянный named volume `kanban_data`.

Если Docker использует старый закэшированный frontend-образ:

```powershell
docker compose build --no-cache frontend
docker compose up
```

## Демо-данные

Маленький seed:

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python scripts\seed.py
```

Создаются пользователи:

| login | password | role |
| --- | --- | --- |
| `owner` | `password123` | owner |
| `editor` | `password123` | editor |
| `viewer` | `password123` | viewer |

Полные моковые данные для презентации:

```powershell
.\.venv\Scripts\Activate.ps1
python backend\scripts\seed_mock_data.py
```

Скрипт создает две демо-доски, если их еще нет:

- `Демо: Фичи`
- `Демо: Найм`

Также создаются демо-пользователи, метки, 10-15 карточек на каждую доску, дедлайны, приоритеты и исполнители. Скрипт идемпотентен по названию доски, поэтому повторный запуск не должен создавать дубликаты этих досок.

Пароль демо-пользователей:

```text
password123
```

Во frontend также есть временная кнопка тестового входа:

```text
login: testuser
password: 123123123
```

Этот пользователь должен существовать в текущей базе данных, иначе кнопка не сможет войти.

## Smoke-сценарий API

При запущенном backend:

```powershell
.\.venv\Scripts\Activate.ps1
python backend\scripts\smoke_api.py --base-url http://127.0.0.1:8000
```

Скрипт регистрирует временного пользователя, логинится, создает доску, колонки, метку, карточку, перемещает карточку, добавляет комментарий и выводит небольшой JSON-результат.

## Тесты

Запуск всех тестов из корня проекта:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest backend/tests frontend/tests
```

Только backend:

```powershell
python -m pytest backend/tests
```

Только frontend:

```powershell
python -m pytest frontend/tests
```

Backend-тесты используют in-memory SQLite и не трогают `backend/kanban.db`.

## API

Авторизация:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Доски:

- `GET /api/tables`
- `POST /api/tables`
- `GET /api/tables/{board_id}`
- `PATCH /api/tables/{board_id}`
- `DELETE /api/tables/{board_id}`
- `GET /api/tables/{board_id}/kanban`

Колонки:

- `GET /api/tables/{board_id}/columns`
- `POST /api/tables/{board_id}/columns`
- `PATCH /api/tables/{board_id}/columns/{column_id}`
- `DELETE /api/tables/{board_id}/columns/{column_id}`

Карточки:

- `GET /api/tables/{board_id}/cards`
- `GET /api/tables/{board_id}/cards/overdue`
- `POST /api/tables/{board_id}/cards`
- `GET /api/tables/{board_id}/cards/{card_id}`
- `PATCH /api/tables/{board_id}/cards/{card_id}`
- `PATCH /api/tables/{board_id}/cards/{card_id}/move`
- `DELETE /api/tables/{board_id}/cards/{card_id}`

Метки:

- `GET /api/tables/{board_id}/labels`
- `POST /api/tables/{board_id}/labels`
- `PATCH /api/tables/{board_id}/labels/{label_id}`
- `DELETE /api/tables/{board_id}/labels/{label_id}`

Роли:

- `GET /api/tables/{board_id}/roles`
- `POST /api/tables/{board_id}/roles`
- `PATCH /api/tables/{board_id}/roles/{user_id}`
- `DELETE /api/tables/{board_id}/roles/{user_id}`

Комментарии:

- `GET /api/tables/{board_id}/cards/{card_id}/comments`
- `POST /api/tables/{board_id}/cards/{card_id}/comments`
- `PATCH /api/tables/{board_id}/cards/{card_id}/comments/{comment_id}`
- `DELETE /api/tables/{board_id}/cards/{card_id}/comments/{comment_id}`

Пользователи:

- `GET /api/users?q=<часть_логина>`

## Права доступа

| Действие | owner | editor | viewer |
| --- | --- | --- | --- |
| Просмотр доски | да | да | да |
| Создание/редактирование/удаление доски | да | нет | нет |
| Управление участниками и ролями | да | нет | нет |
| Создание/редактирование/удаление колонок | да | да | нет |
| Создание/редактирование/удаление/перемещение карточек | да | да | нет |
| Назначение исполнителя, дедлайна, приоритета и меток | да | да | нет |
| Создание комментариев | да | да | нет |
| Просмотр комментариев | да | да | да |

Frontend скрывает недоступные кнопки изменения для роли `viewer`.

## Заметки

- Flet закреплен на версии `0.85.3`.
- Docker frontend использует `KANBAN_FLET_VIEW=web_browser` и `FLET_FORCE_WEB_SERVER=true`, чтобы Flet не пытался запускать desktop-клиент внутри Linux-контейнера.
- Фоновое обновление доски сделано простым polling-механизмом для MVP/демо: frontend периодически обновляет текущую доску, если пользователь не редактирует поле и в панели карточки нет несохраненных изменений.
