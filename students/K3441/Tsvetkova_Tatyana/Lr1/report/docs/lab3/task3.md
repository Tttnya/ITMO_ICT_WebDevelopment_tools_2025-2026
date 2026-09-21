# Подзадача 3 — Вызов парсера через очередь (Celery + Redis)

Основное API ставит задачу парсинга в очередь и **сразу** отвечает
клиенту `task_id`, не дожидаясь, пока страница скачается — сам парсинг
выполняет отдельный контейнер `worker` (Celery), а Redis выступает
брокером сообщений и хранилищем результатов.

## Конфигурация Celery

```python title="app/celery_app.py" linenums="1"
"""Конфигурация Celery: Redis как брокер и хранилище результатов
(лабораторная работа №3, подзадача 3)."""
import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", broker_url)

celery_app = Celery("bookcrossing", broker=broker_url, backend=result_backend)
celery_app.conf.task_track_started = True
celery_app.autodiscover_tasks(["app.parsing"])
```

## Задача

Переиспользует ту же функцию `parse_and_save`, что и HTTP-сервис
парсера из [Подзадачи 2](task2.md) — отличается только значением
`approach`.

```python title="app/parsing/tasks.py" linenums="1"
from ..celery_app import celery_app
from .service import parse_and_save


@celery_app.task(name="app.parsing.tasks.parse_url_task")
def parse_url_task(url: str) -> dict:
    page = parse_and_save(url=url, approach="celery")
    return {
        "id": page.id,
        "url": page.url,
        "title": page.title,
        "approach": page.approach,
        "created_at": page.created_at.isoformat(),
    }
```

## Эндпоинты постановки в очередь и опроса статуса

```python title="app/parsing/router.py" linenums="1"
@router.post("/async", response_model=ParseTaskAccepted)
def parse_async(payload: ParseRequest) -> ParseTaskAccepted:
    """Подзадача 3: ставит задачу парсинга в очередь Celery/Redis
    и сразу отвечает клиенту, не дожидаясь выполнения."""
    task = parse_url_task.delay(payload.url)
    return ParseTaskAccepted(task_id=task.id, status="queued")


@router.get("/async/{task_id}", response_model=ParseTaskStatus)
def parse_async_status(task_id: str) -> ParseTaskStatus:
    result = AsyncResult(task_id, app=celery_app)

    if result.failed():
        raise HTTPException(status_code=500, detail=str(result.result))

    return ParseTaskStatus(
        task_id=task_id,
        status=result.status,
        result=result.result if result.successful() else None,
    )
```

## Воркер в docker-compose

`worker` — тот же образ, что и `api` (тот же `Dockerfile`), но с другой
командой запуска и `SKIP_MIGRATIONS=1` (схему БД мигрирует только `api`,
см. [Подзадачу 1](task1.md)):

```yaml
worker:
  build:
    context: .
    dockerfile: Dockerfile
  command: celery -A app.celery_app:celery_app worker --loglevel=info
  environment:
    CELERY_BROKER_URL: redis://redis:6379/0
    CELERY_RESULT_BACKEND: redis://redis:6379/0
    SKIP_MIGRATIONS: "1"
```

!!! note "`-A app.celery_app:celery_app`, а не `-A app.celery_app`"
    Без явного указания атрибута через `:celery_app` Celery CLI ищет
    внутри модуля `app.celery_app` переменную с именем `app` или
    `celery` (стандартная конвенция) — а у нас Celery-инстанс называется
    `celery_app`. Явный `module:attr` исключает эту неоднозначность.

## Проверка

```bash
curl -X POST http://localhost:8000/parsing/async \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org/3/"}'
```

```json title="Ответ приходит мгновенно"
{"task_id": "8310fcb4-994d-4ef2-91a3-985a858fc427", "status": "queued"}
```

```bash
curl http://localhost:8000/parsing/async/8310fcb4-994d-4ef2-91a3-985a858fc427
```

```json title="После того как worker забрал задачу"
{
  "task_id": "8310fcb4-994d-4ef2-91a3-985a858fc427",
  "status": "SUCCESS",
  "result": {
    "id": 2,
    "url": "https://docs.python.org/3/",
    "title": "3.14.7 Documentation",
    "approach": "celery",
    "created_at": "2026-09-21T16:56:59.068368"
  }
}
```

Логи воркера (`docker compose logs worker`) показывают, что задача
реально обрабатывается в отдельном процессе, а не в процессе `api`:

```
worker-1  | [INFO] Task app.parsing.tasks.parse_url_task[8310fcb4-...] received
worker-1  | [INFO] Task app.parsing.tasks.parse_url_task[8310fcb4-...] succeeded
```

## Итог: два способа вызова парсера бок о бок

```bash
docker compose exec db psql -U postgres -d bookcrossing_db \
  -c "select id, url, title, approach, created_at from parsed_page order by id;"
```

| id | url                          | approach       |
|---:|-------------------------------|-----------------|
| 1  | `https://www.python.org`      | `sync-service`  |
| 2  | `https://docs.python.org/3/`  | `celery`        |

Оба пути пишут в одну и ту же таблицу, используя одну и ту же функцию
парсинга — различаются только тем, как эта функция вызывается: напрямую
по HTTP (блокирующий запрос, ответ сразу содержит результат) или через
очередь (мгновенный ответ с `task_id`, результат появляется позже).
