# Подзадача 1 — Упаковка в Docker

Нужно было упаковать в Docker основное FastAPI-приложение (ЛР1), базу
данных и парсер (ЛР2), причём парсер должен быть вызываемым по HTTP из
отдельного контейнера — то есть фактически два отдельных приложения:
`api` (ЛР1 + новые эндпоинты) и `parser` (отдельный FastAPI-сервис).

## docker-compose.yml

```yaml title="docker-compose.yml" linenums="1"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: bookcrossing_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: "123"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

  parser:
    build:
      context: .
      dockerfile: parser_service/Dockerfile
    environment:
      DB_ADMIN: postgresql://postgres:123@db:5432/bookcrossing_db
      SKIP_MIGRATIONS: "1"
    ports:
      - "8001:8001"
    depends_on:
      db:
        condition: service_healthy

  api:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DB_ADMIN: postgresql://postgres:123@db:5432/bookcrossing_db
      JWT_SECRET: dev-secret-change-in-production-please
      JWT_ALGORITHM: HS256
      JWT_EXPIRE_MINUTES: "60"
      PARSER_SERVICE_URL: http://parser:8001
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      parser:
        condition: service_started

  worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.celery_app:celery_app worker --loglevel=info
    environment:
      DB_ADMIN: postgresql://postgres:123@db:5432/bookcrossing_db
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      SKIP_MIGRATIONS: "1"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  pgdata:
```

## Dockerfile (api / worker)

`api` и `worker` — одна и та же кодовая база и один и тот же образ,
отличаются только командой запуска (`docker-compose.yml` переопределяет
`command:` для `worker`).

```dockerfile title="Dockerfile" linenums="1"
FROM python:3.11-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash title="entrypoint.sh" linenums="1"
#!/bin/sh
set -e

if [ "$SKIP_MIGRATIONS" != "1" ]; then
  alembic upgrade head
fi

exec "$@"
```

!!! warning "Миграции — только в одном контейнере"
    Первая версия компоновки давала обеим сторонам (`parser` и `api`)
    самостоятельно создавать схему БД: `parser` вызывал
    `SQLModel.metadata.create_all()` на старте, а `api` параллельно
    накатывал Alembic-миграции — получалась гонка `relation "book"
    already exists`. Исправлено так, что схему создаёт и мигрирует
    **только** `api` (`entrypoint.sh` → `alembic upgrade head`), а
    `parser`/`worker` запускаются с `SKIP_MIGRATIONS=1` и просто
    работают с уже готовой БД.

## Dockerfile парсера (отдельный сервис)

```dockerfile title="parser_service/Dockerfile" linenums="1"
FROM python:3.11-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY parser_service ./parser_service

EXPOSE 8001

CMD ["uvicorn", "parser_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

```python title="parser_service/main.py" linenums="1"
"""Отдельное FastAPI-приложение с парсером (лабораторная работа №3,
подзадача 1, пункт 4). Запускается в собственном Docker-контейнере,
принимает URL и сохраняет результат в общую базу данных.

Схему базы (включая таблицу parsed_page) создаёт и мигрирует только
контейнер `api` через Alembic — здесь схема не трогается, чтобы не
гоняться с миграциями api за право первым создать таблицы.
"""
from fastapi import FastAPI, HTTPException
from requests import RequestException

from app.parsing.schemas import ParseRequest
from app.parsing.service import parse_and_save

app = FastAPI(title="Bookcrossing Parser Service", version="1.0.0")


@app.get("/", tags=["root"])
def root() -> dict:
    return {"service": "parser", "status": "ok"}


@app.post("/parse")
def parse(payload: ParseRequest) -> dict:
    try:
        page = parse_and_save(url=payload.url, approach="sync-service")
    except RequestException as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "id": page.id,
        "url": page.url,
        "title": page.title,
        "approach": page.approach,
        "created_at": page.created_at.isoformat(),
    }
```

Обратите внимание: `parser_service/main.py` **не содержит** своей копии
логики парсинга — он импортирует общую функцию `parse_and_save` из
`app/parsing/service.py` (см. [Подзадачу 2](task2.md)), той же, что
использует и Celery-воркер в [Подзадаче 3](task3.md).

## Проверка

```bash
docker compose ps
```

```
NAME                    STATUS
bookcrossing-api-1      Up (0.0.0.0:8000->8000/tcp)
bookcrossing-db-1       Up (healthy)
bookcrossing-parser-1   Up (0.0.0.0:8001->8001/tcp)
bookcrossing-redis-1    Up (healthy)
bookcrossing-worker-1   Up
```

Все 5 сервисов поднимаются одной командой `docker compose up --build`.
