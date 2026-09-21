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
