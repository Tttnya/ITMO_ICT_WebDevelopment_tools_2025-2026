"""Задача 2: параллельный парсинг веб-страниц через async/await (aiohttp).

Один поток, один процесс — но пока ждём ответ от одного сервера, event
loop уже отправляет запрос к следующему. Запись в SQLite синхронна, но
занимает пренебрежимо мало времени по сравнению с сетевым ожиданием.
"""
from __future__ import annotations

import argparse
import asyncio
import time

import aiohttp
from bs4 import BeautifulSoup
from sqlmodel import Session

from db import ParsedPage, get_engine, init_db
from urls import HEADERS, URLS, split_into_chunks

APPROACH = "async"
DEFAULT_WORKERS = 3


async def parse_and_save(session: aiohttp.ClientSession, url: str) -> None:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
        html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    engine = get_engine()
    with Session(engine) as db_session:
        db_session.add(ParsedPage(url=url, title=title, approach=APPROACH))
        db_session.commit()

    print(f"[{APPROACH}] {url} -> {title}")


async def _worker(session: aiohttp.ClientSession, urls_chunk: list[str]) -> None:
    for url in urls_chunk:
        await parse_and_save(session, url)


async def run(urls: list[str], workers: int = DEFAULT_WORKERS) -> None:
    chunks = split_into_chunks(urls, workers)
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        await asyncio.gather(*(_worker(session, chunk) for chunk in chunks))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Параллельный парсинг через asyncio/aiohttp")
    parser.add_argument("--urls", nargs="*", default=URLS)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="число задач (URL делятся на равные части)")
    args = parser.parse_args()

    init_db()
    started = time.perf_counter()
    asyncio.run(run(args.urls, args.workers))
    elapsed = time.perf_counter() - started

    print(f"async: обработано {len(args.urls)} URL за {elapsed:.4f} сек, задач={args.workers}")
