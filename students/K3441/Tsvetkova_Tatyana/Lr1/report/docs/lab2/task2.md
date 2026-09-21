# Задача 2 — Параллельный парсинг веб-страниц

Каждая программа делает `parse_and_save(url)`:

1. Скачивает HTML по URL.
2. Достаёт `<title>` через `BeautifulSoup`.
3. Сохраняет `(url, title, approach, parsed_at)` в БД (`parsed_page`).
4. Печатает результат в консоль.

## База данных

Используется та же база, что в ЛР1 (`bookcrossing.db`, подключение из
`.env` → `DB_ADMIN`). Существующие таблицы буккроссинга к произвольному
парсингу не относятся, поэтому заведена **отдельная таблица** `parsed_page`
— её создаёт `init_db()` в [`task2/db.py`](https://github.com/Tttnya/ITMO_ICT_WebDevelopment_tools_2025-2026/blob/main/students/K3441/Tsvetkova_Tatyana/Lr2/task2/db.py):

| Поле        | Тип       | Описание                                       |
|-------------|-----------|------------------------------------------------|
| `id`        | int, PK   | автоинкремент                                  |
| `url`       | str       | адрес страницы                                 |
| `title`     | str       | содержимое `<title>`                           |
| `approach`  | str       | `threading` / `multiprocessing` / `async`      |
| `parsed_at` | datetime  | момент сохранения (UTC)                        |

!!! info "Соединения на каждый поток/процесс"
    `get_engine()` вызывается заново на каждый `parse_and_save`, чтобы
    не делить одно соединение SQLite между разными потоками/процессами
    (SQLite-соединения не потокобезопасны по умолчанию).

## Список URL

`example.com`, `python.org`, `docs.python.org/3`, `wikipedia.org`,
`iana.org/domains/reserved`, `httpbin.org`, `w3.org` — 7 публичных
страниц с разным временем ответа. Список делится на **равные части**
между воркерами (`split_into_chunks` в `urls.py`): каждый
поток/процесс/корутина получает свой кусок и обходит его
последовательно через `parse_and_save(url)`.

## Результаты замеров (7 URL, 3 воркера)

| Подход             | Время         | 7 заголовков в БД |
|--------------------|--------------:|:------------------|
| `threading`        | **3.37 сек**  | ✅                |
| `multiprocessing`  | **3.35 сек**  | ✅                |
| `async / aiohttp`  | **2.99 сек**  | ✅                |

## Почему такие результаты

Парсинг страниц — задача **I/O-bound**: большую часть времени программа
не считает, а ждёт ответ от сервера. Картина обратная задаче 1:

* **`threading`** здесь **реально ускоряет работу**: во время ожидания
  сети GIL освобождается, и другой поток может параллельно отправить
  свой запрос. 3 потока обрабатывают свои части списка (по 2-3 URL)
  одновременно, а не все 7 запросов последовательно.
* **`multiprocessing`** тоже параллелит запросы, но каждый процесс — это
  отдельный интерпретатор Python с накладными расходами на старт и
  сериализацию. Для лёгких I/O-задач часто **не быстрее threading**.
* **`async/aiohttp`** — **самый быстрый**: один поток, один процесс, но
  внутри каждого из 3 воркеров `aiohttp` не блокируется на ожидании
  ответа — переключается на другую задачу, пока сеть отвечает — без
  затрат на создание потоков/процессов ОС.

## Код

=== "db.py"

    ```python title="lab2/task2/db.py" linenums="1"
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
    ```

=== "urls.py"

    ```python title="lab2/task2/urls.py" linenums="1"
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
    ```

=== "parse_threading.py"

    ```python title="lab2/task2/parse_threading.py" linenums="1"
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
        parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
        args = parser.parse_args()

        init_db()
        started = time.perf_counter()
        run(args.urls, args.workers)
        elapsed = time.perf_counter() - started

        print(f"threading: обработано {len(args.urls)} URL за {elapsed:.4f} сек, потоков={args.workers}")
    ```

=== "parse_multiprocessing.py"

    ```python title="lab2/task2/parse_multiprocessing.py" linenums="1"
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
        parser.add_argument("--workers", type=int, default=3)
        args = parser.parse_args()

        init_db()
        started = time.perf_counter()
        with multiprocessing.Pool(processes=args.workers) as pool:
            pool.map(parse_and_save, args.urls)
        elapsed = time.perf_counter() - started

        print(f"multiprocessing: обработано {len(args.urls)} URL за {elapsed:.4f} сек, процессов={args.workers}")
    ```

=== "parse_async.py"

    ```python title="lab2/task2/parse_async.py" linenums="1"
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
        parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
        args = parser.parse_args()

        init_db()
        started = time.perf_counter()
        asyncio.run(run(args.urls, args.workers))
        elapsed = time.perf_counter() - started

        print(f"async: обработано {len(args.urls)} URL за {elapsed:.4f} сек, задач={args.workers}")
    ```

## Общий вывод

Для **CPU-bound** кода нужен `multiprocessing` (обход GIL реальными
процессами). Для **I/O-bound** (сеть, диск, внешние API) выигрывают
`threading` и особенно `async/asyncio` за счёт дешёвого переключения
задач во время ожидания, при этом `asyncio` обычно эффективнее по
накладным расходам, чем потоки ОС.
