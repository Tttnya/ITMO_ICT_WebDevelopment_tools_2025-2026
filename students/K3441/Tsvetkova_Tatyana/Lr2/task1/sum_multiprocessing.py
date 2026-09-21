"""Задача 1: сумма чисел от 1 до N через multiprocessing.

В отличие от threading, отдельные процессы не разделяют GIL, поэтому
вычисления реально распределяются по ядрам процессора.
"""
from __future__ import annotations

import argparse
import multiprocessing
import time

DEFAULT_N = 10**13
DEFAULT_WORKERS = 8


def _partial_sum(bounds: tuple[int, int]) -> int:
    start, end = bounds
    return sum(range(start, end))


def calculate_sum(n: int = DEFAULT_N, workers: int = DEFAULT_WORKERS) -> int:
    chunk = n // workers
    bounds = []
    start = 1
    for i in range(workers):
        end = start + chunk if i < workers - 1 else n + 1
        bounds.append((start, end))
        start = end

    with multiprocessing.Pool(processes=workers) as pool:
        partials = pool.map(_partial_sum, bounds)

    return sum(partials)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сумма 1..N через multiprocessing")
    parser.add_argument("--n", type=int, default=DEFAULT_N, help="верхняя граница (по умолчанию 10**13)")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="число процессов")
    args = parser.parse_args()

    started = time.perf_counter()
    total = calculate_sum(args.n, args.workers)
    elapsed = time.perf_counter() - started

    print(f"multiprocessing: N={args.n}, процессов={args.workers}")
    print(f"Сумма = {total}")
    print(f"Время выполнения: {elapsed:.4f} сек")
