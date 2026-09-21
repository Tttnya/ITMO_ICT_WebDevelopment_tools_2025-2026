"""Задача 1: сумма чисел от 1 до N через async/await (asyncio).

asyncio даёт кооперативную многозадачность в одном потоке: реального
параллелизма для CPU-bound кода нет (как и у threading, только без потоков
ОС), поэтому суммирование каждого куска дробится на мелкие шаги с
await asyncio.sleep(0), чтобы event loop мог переключаться между задачами.
"""
from __future__ import annotations

import argparse
import asyncio
import time

DEFAULT_N = 10**13
DEFAULT_WORKERS = 8


async def _partial_sum(start: int, end: int) -> int:
    total = 0
    step = max((end - start) // 100, 1)
    cursor = start
    while cursor < end:
        nxt = min(cursor + step, end)
        total += sum(range(cursor, nxt))
        cursor = nxt
        await asyncio.sleep(0)
    return total


async def _calculate_sum_async(n: int, workers: int) -> int:
    chunk = n // workers
    tasks = []
    start = 1
    for i in range(workers):
        end = start + chunk if i < workers - 1 else n + 1
        tasks.append(_partial_sum(start, end))
        start = end
    partials = await asyncio.gather(*tasks)
    return sum(partials)


def calculate_sum(n: int = DEFAULT_N, workers: int = DEFAULT_WORKERS) -> int:
    return asyncio.run(_calculate_sum_async(n, workers))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сумма 1..N через asyncio")
    parser.add_argument("--n", type=int, default=DEFAULT_N, help="верхняя граница (по умолчанию 10**13)")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="число задач (task)")
    args = parser.parse_args()

    started = time.perf_counter()
    total = calculate_sum(args.n, args.workers)
    elapsed = time.perf_counter() - started

    print(f"async: N={args.n}, задач={args.workers}")
    print(f"Сумма = {total}")
    print(f"Время выполнения: {elapsed:.4f} сек")
