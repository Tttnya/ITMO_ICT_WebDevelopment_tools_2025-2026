"""Задача 1: сумма чисел от 1 до N через threading.

Из-за GIL потоки в CPython не дают параллелизма для CPU-bound кода —
скрипт нужен, чтобы наглядно это показать (см. lab2/README.md).
"""
from __future__ import annotations

import argparse
import threading
import time

DEFAULT_N = 10**13
DEFAULT_WORKERS = 8


def _partial_sum(start: int, end: int, results: list[int], index: int) -> None:
    results[index] = sum(range(start, end))


def calculate_sum(n: int = DEFAULT_N, workers: int = DEFAULT_WORKERS) -> int:
    chunk = n // workers
    results = [0] * workers
    threads = []
    start = 1
    for i in range(workers):
        end = start + chunk if i < workers - 1 else n + 1
        t = threading.Thread(target=_partial_sum, args=(start, end, results, i))
        threads.append(t)
        start = end

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return sum(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сумма 1..N через threading")
    parser.add_argument("--n", type=int, default=DEFAULT_N, help="верхняя граница (по умолчанию 10**13)")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="число потоков")
    args = parser.parse_args()

    started = time.perf_counter()
    total = calculate_sum(args.n, args.workers)
    elapsed = time.perf_counter() - started

    print(f"threading: N={args.n}, потоков={args.workers}")
    print(f"Сумма = {total}")
    print(f"Время выполнения: {elapsed:.4f} сек")
