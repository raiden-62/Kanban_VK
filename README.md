# VK Kanban

MVP Kanban-проекта: FastAPI backend, позже Flet frontend.

## Python

Используем Python 3.12. Виртуальное окружение держим в корне проекта:

```text
Kanban_VK/
  .venv/
  backend/
```

## Установка зависимостей

Из корня проекта:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

В одном `requirements.txt` лежат runtime- и test-зависимости проекта.

## Запуск тестов

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python -m pytest
```

## Запуск backend

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`
