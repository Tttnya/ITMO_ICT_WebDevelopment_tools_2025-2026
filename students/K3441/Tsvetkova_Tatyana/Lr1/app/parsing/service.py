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
