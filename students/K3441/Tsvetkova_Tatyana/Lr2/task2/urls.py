"""Список URL для параллельного парсинга (Задача 2)."""
from __future__ import annotations

URLS = [
    "https://example.com",
    "https://www.python.org",
    "https://docs.python.org/3/",
    "https://www.wikipedia.org/",
    "https://www.iana.org/domains/reserved",
    "https://httpbin.org/",
    "https://www.w3.org/",
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LabScraper/1.0)"}


def split_into_chunks(urls: list[str], workers: int) -> list[list[str]]:
    """Делит список URL на `workers` примерно равных частей (без пустых)."""
    workers = max(1, min(workers, len(urls)))
    chunks: list[list[str]] = [[] for _ in range(workers)]
    for i, url in enumerate(urls):
        chunks[i % workers].append(url)
    return [chunk for chunk in chunks if chunk]
