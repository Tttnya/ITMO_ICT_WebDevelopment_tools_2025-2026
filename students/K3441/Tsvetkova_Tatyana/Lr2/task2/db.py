"""Общая модель БД для задачи 2.

Результаты парсинга сохраняются в ту же базу данных, что использовалась
в лабораторной работе №1 (bookcrossing.db / DB_ADMIN из .env), в новую
таблицу parsed_page — отдельную от таблиц буккроссинга (user, book, ...),
чтобы не смешивать предметные области.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from sqlmodel import Field, SQLModel, create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

_raw_url = os.getenv("DB_ADMIN", "sqlite:///./bookcrossing.db")
if _raw_url.startswith("sqlite:///./"):
    # относительный путь из .env считаем от корня проекта bookcrossing/
    DB_URL = f"sqlite:///{PROJECT_ROOT / _raw_url.removeprefix('sqlite:///./')}"
else:
    DB_URL = _raw_url


class ParsedPage(SQLModel, table=True):
    __tablename__ = "parsed_page"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    title: str
    approach: str  # threading / multiprocessing / async
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


def get_engine():
    """Новый engine на каждый вызов — свои соединения на поток/процесс."""
    connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
    return create_engine(DB_URL, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(get_engine())
