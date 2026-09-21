import os

import requests
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

from ..celery_app import celery_app
from .schemas import ParseRequest, ParseResult, ParseTaskAccepted, ParseTaskStatus
from .tasks import parse_url_task

router = APIRouter(prefix="/parsing", tags=["parsing"])

PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://localhost:8001")


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
