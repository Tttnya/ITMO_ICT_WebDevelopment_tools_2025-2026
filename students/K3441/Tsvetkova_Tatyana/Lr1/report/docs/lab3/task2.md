# Подзадача 2 — Вызов парсера из FastAPI по HTTP

Клиент отправляет URL основному API (`api`), оно **синхронно**
обращается по HTTP к контейнеру `parser` и возвращает результат клиенту
— пример из методички (эндпоинт `/parse` через `requests` +
`HTTPException`) реализован именно так: как отдельный сервис-парсер,
к которому основное приложение ходит по сети.

## Общая логика парсинга

Вынесена в отдельный модуль, чтобы её использовали и HTTP-сервис
(эта подзадача), и Celery-задача ([Подзадача 3](task3.md)) — без
дублирования кода `requests` + `BeautifulSoup` из ЛР2.

```python title="app/parsing/service.py" linenums="1"
"""Общая логика парсинга страницы, используемая и HTTP-сервисом парсера,
и Celery-воркером — чтобы не дублировать код (лабораторная работа №3).
"""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from sqlmodel import Session

from ..connection import engine
from ..models import ParsedPage

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LabScraper/1.0)"}


def fetch_title(url: str) -> str:
    """Скачивает страницу по `url` и возвращает текст тега <title>."""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    return soup.title.string.strip() if soup.title and soup.title.string else url


def save_parsed_page(url: str, title: str, approach: str) -> ParsedPage:
    with Session(engine) as session:
        page = ParsedPage(url=url, title=title, approach=approach)
        session.add(page)
        session.commit()
        session.refresh(page)
        return page


def parse_and_save(url: str, approach: str) -> ParsedPage:
    title = fetch_title(url)
    return save_parsed_page(url=url, title=title, approach=approach)
```

Результат пишется в таблицу `parsed_page` (та же модель, что в ЛР2,
теперь — часть основной схемы `app/models.py`):

| Поле         | Тип       | Описание                                      |
|--------------|-----------|------------------------------------------------|
| `id`         | int, PK   | автоинкремент                                   |
| `url`        | str       | адрес страницы                                  |
| `title`      | str       | содержимое `<title>`                            |
| `approach`   | str       | `sync-service` (эта подзадача) / `celery`       |
| `created_at` | datetime  | момент сохранения (UTC)                         |

## Эндпоинт в основном приложении

```python title="app/parsing/router.py" linenums="1"
@router.post("/sync", response_model=ParseResult)
def parse_sync(payload: ParseRequest) -> ParseResult:
    """Подзадача 2: принимает URL от клиента, синхронно вызывает
    отдельный HTTP-сервис парсера (запущенный в другом контейнере)
    и возвращает результат клиенту."""
    try:
        response = requests.post(
            f"{PARSER_SERVICE_URL}/parse", json={"url": payload.url}, timeout=15
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Сервис парсера недоступен: {exc}")

    return response.json()
```

`PARSER_SERVICE_URL` берётся из переменной окружения — внутри Docker-сети
это `http://parser:8001` (имя контейнера как хост, см.
`docker-compose.yml` в [Подзадаче 1](task1.md)), при локальном запуске
без Docker — `http://localhost:8001`.

## Проверка

Через Swagger UI (`http://localhost:8000/docs` → `POST /parsing/sync` →
Try it out → Execute) или `curl`:

```bash
curl -X POST http://localhost:8000/parsing/sync \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.python.org"}'
```

```json title="Ответ 200"
{
  "id": 1,
  "url": "https://www.python.org",
  "title": "Welcome to Python.org",
  "approach": "sync-service",
  "created_at": "2026-09-21T16:56:44.760003"
}
```

Если контейнер `parser` недоступен, `api` не падает, а корректно
отвечает `502` с деталями ошибки:

```json title="Ответ 502 (parser недоступен)"
{
  "detail": "Сервис парсера недоступен: HTTPConnectionPool(host='parser', port=8001): Max retries exceeded ..."
}
```
