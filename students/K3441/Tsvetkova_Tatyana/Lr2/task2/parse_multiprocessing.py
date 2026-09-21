"""Задача 2: параллельный парсинг веб-страниц через multiprocessing.

Каждый URL обрабатывается в отдельном процессе. Для I/O-bound задачи это
даёт такое же ускорение, как threading, но с накладными расходами на
старт процессов и отсутствием общей памяти (каждый процесс открывает
собственное соединение с БД через get_engine()).
"""
from __future__ import annotations

import argparse
import multiprocessing
import time

import requests
from bs4 import BeautifulSoup
from sqlmodel import Session

from db import ParsedPage, get_engine, init_db
from urls import HEADERS, URLS

APPROACH = "multiprocessing"


def parse_and_save(url: str) -> str:
    response = requests.get(url, timeout=10, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    engine = get_engine()
    with Session(engine) as session:
        session.add(ParsedPage(url=url, title=title, approach=APPROACH))
        session.commit()
    engine.dispose()

    message = f"[{APPROACH}] {url} -> {title}"
    print(message)
    return message


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Параллельный парсинг через multiprocessing")
    parser.add_argument("--urls", nargs="*", default=URLS)
    parser.add_argument("--workers", type=int, default=3, help="число процессов (URL делятся на равные части через Pool.map)")
    args = parser.parse_args()

    init_db()
    started = time.perf_counter()
    with multiprocessing.Pool(processes=args.workers) as pool:
        pool.map(parse_and_save, args.urls)
    elapsed = time.perf_counter() - started

    print(f"multiprocessing: обработано {len(args.urls)} URL за {elapsed:.4f} сек, процессов={args.workers}")
