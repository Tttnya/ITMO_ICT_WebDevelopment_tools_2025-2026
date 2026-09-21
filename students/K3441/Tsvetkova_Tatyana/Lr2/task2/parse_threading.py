"""Задача 2: параллельный парсинг веб-страниц через threading.

Парсинг — это I/O-bound задача (ожидание сети), поэтому здесь потоки
дают реальное ускорение: пока один поток ждёт ответ сервера, GIL
освобождается и работает другой поток.
"""
from __future__ import annotations

import argparse
import threading
import time

import requests
from bs4 import BeautifulSoup
from sqlmodel import Session

from db import ParsedPage, get_engine, init_db
from urls import HEADERS, URLS, split_into_chunks

APPROACH = "threading"
DEFAULT_WORKERS = 3


def parse_and_save(url: str) -> None:
    response = requests.get(url, timeout=10, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    engine = get_engine()
    with Session(engine) as session:
        session.add(ParsedPage(url=url, title=title, approach=APPROACH))
        session.commit()

    print(f"[{APPROACH}] {url} -> {title}")


def _worker(urls_chunk: list[str]) -> None:
    for url in urls_chunk:
        parse_and_save(url)


def run(urls: list[str], workers: int = DEFAULT_WORKERS) -> None:
    chunks = split_into_chunks(urls, workers)
    threads = [threading.Thread(target=_worker, args=(chunk,)) for chunk in chunks]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Параллельный парсинг через threading")
    parser.add_argument("--urls", nargs="*", default=URLS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="число потоков (URL делятся на равные части)")
    args = parser.parse_args()

    init_db()
    started = time.perf_counter()
    run(args.urls, args.workers)
    elapsed = time.perf_counter() - started

    print(f"threading: обработано {len(args.urls)} URL за {elapsed:.4f} сек, потоков={args.workers}")
