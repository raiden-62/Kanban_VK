FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV KANBAN_FLET_HOST=0.0.0.0
ENV KANBAN_FLET_PORT=8550
ENV KANBAN_FLET_VIEW=web_browser
ENV FLET_FORCE_WEB_SERVER=true

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend ./frontend

EXPOSE 8550

CMD ["python", "-m", "frontend.app.main"]
