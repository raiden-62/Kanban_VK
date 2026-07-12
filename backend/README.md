# VK Kanban Backend

FastAPI backend для MVP Kanban-доски.

## Возможности

- Регистрация и логин пользователя.
- JWT-токен для доступа к защищенным ручкам.
- CRUD досок (`tables`).
- Участники доски и роли: `owner`, `editor`, `viewer`.
- CRUD колонок.
- CRUD карточек.
- Перемещение карточек между колонками и изменение порядка.
- Назначение исполнителя и дедлайн.
- Комментарии к карточкам.

## Версия Python

Рекомендуемая версия: Python 3.12.

## Расположение virtualenv

Virtualenv держим в корне проекта:

```text
Kanban_VK/
  .venv/
  backend/
  frontend/
```

Так один interpreter можно использовать и для backend, и для будущего Flet frontend.

## Установка

Из корня проекта:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

В одном корневом `requirements.txt` лежат runtime- и test-зависимости проекта.

## Запуск API

Из корня проекта:

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn app.main:app --reload
```

После запуска:

- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Наполнение демо-данными

Из корня проекта:

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python scripts\seed.py
```

Будут созданы пользователи:

| login | password | role |
| --- | --- | --- |
| owner | password123 | owner |
| editor | password123 | editor |
| viewer | password123 | viewer |

## Авторизация

1. `POST /api/auth/register`
2. `POST /api/auth/login`
3. Скопировать `access_token`.
4. Для остальных запросов передавать заголовок:

```http
Authorization: Bearer <access_token>
```

Пароли хранятся только в виде bcrypt-хэша.

## Тесты

Из корня проекта:

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python -m pytest
```

Тесты используют отдельную in-memory SQLite базу и не трогают `kanban.db`.
