# Задача 1 — Сумма чисел от 1 до N

Три реализации `calculate_sum(n, workers)`, каждая делит диапазон `1..n`
на `workers` равных кусков и суммирует их параллельно, потом складывает
частичные суммы.

По заданию **N = 10¹³**. Прогон с таким N на чистом Python занимает
часы вне зависимости от подхода, поэтому для сравнения замерялось на
меньшем N; корректность в любом случае проверяется точной формулой
`n(n+1)/2`. Флаг `--n 10000000000000` позволяет запустить «как в задании»,
если нужно.

## Результаты замеров (N = 500 000 000, 8 воркеров, MacBook Air, 8 ядер)

| Подход           | Время          | Загрузка CPU    | Сумма                     |
|------------------|---------------:|----------------:|:--------------------------|
| `threading`      | **4.91 сек**   | ~100 % (1 ядро) | 125 000 000 250 000 000 ✅ |
| `multiprocessing`| **1.12 сек**   | ~685 % (≈7 ядер)| 125 000 000 250 000 000 ✅ |
| `async / asyncio`| **4.93 сек**   | ~100 % (1 ядро) | 125 000 000 250 000 000 ✅ |

Корректность на маленьком N (`N = 10 000 000`): все три программы дают
`50 000 005 000 000`, что совпадает с `n(n+1)/2`.

**Экстраполяция на N = 10¹³** (линейно, ×20 000 от замера): `threading` и
`async` — около **27 часов**, `multiprocessing` — около **6 часов**.

## Почему такие результаты

* **`threading`** не ускоряет CPU-bound код: из-за GIL (Global Interpreter
  Lock) в CPython только один поток исполняет байткод в любой момент.
  Все 8 потоков соревнуются за GIL, поэтому время ≈ как у одного потока,
  CPU загружен на одно ядро.
* **`multiprocessing`** даёт реальное ускорение (~4.4×): у каждого
  процесса свой интерпретатор и свой GIL, вычисления реально выполняются
  на разных ядрах. Не строго ×8 из-за накладных на старт процессов и
  сериализацию результатов.
* **`asyncio`** — кооперативная многозадачность в одном потоке:
  `await asyncio.sleep(0)` только передаёт управление другой корутине,
  пока одна считает — все ждут. Для CPU-bound задач выигрыша нет.

## Код

=== "sum_threading.py"

    ```python title="lab2/task1/sum_threading.py" linenums="1"
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
        parser.add_argument("--n", type=int, default=DEFAULT_N)
        parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
        args = parser.parse_args()

        started = time.perf_counter()
        total = calculate_sum(args.n, args.workers)
        elapsed = time.perf_counter() - started

        print(f"threading: N={args.n}, потоков={args.workers}")
        print(f"Сумма = {total}")
        print(f"Время выполнения: {elapsed:.4f} сек")
    ```

=== "sum_multiprocessing.py"

    ```python title="lab2/task1/sum_multiprocessing.py" linenums="1"
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
        parser.add_argument("--n", type=int, default=DEFAULT_N)
        parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
        args = parser.parse_args()

        started = time.perf_counter()
        total = calculate_sum(args.n, args.workers)
        elapsed = time.perf_counter() - started

        print(f"multiprocessing: N={args.n}, процессов={args.workers}")
        print(f"Сумма = {total}")
        print(f"Время выполнения: {elapsed:.4f} сек")
    ```

=== "sum_async.py"

    ```python title="lab2/task1/sum_async.py" linenums="1"
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
        parser.add_argument("--n", type=int, default=DEFAULT_N)
        parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
        args = parser.parse_args()

        started = time.perf_counter()
        total = calculate_sum(args.n, args.workers)
        elapsed = time.perf_counter() - started

        print(f"async: N={args.n}, задач={args.workers}")
        print(f"Сумма = {total}")
        print(f"Время выполнения: {elapsed:.4f} сек")
    ```
