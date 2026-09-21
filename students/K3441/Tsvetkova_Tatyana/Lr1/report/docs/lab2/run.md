# Запуск ЛР2

Продолжение проекта ЛР1 — используется то же виртуальное окружение и та
же база данных.

## Установка (одна команда)

```bash
cd bookcrossing
source .venv/bin/activate
pip install -r requirements.txt   # добавлены requests, aiohttp, beautifulsoup4
```

## Задача 1 — сумма чисел

```bash
cd lab2/task1
python3 sum_threading.py       --n 500000000 --workers 8
python3 sum_multiprocessing.py --n 500000000 --workers 8
python3 sum_async.py           --n 500000000 --workers 8
```

Флаги:

* `--n <число>` — верхняя граница (по умолчанию `10**13` — задание, но
  практически считается часами).
* `--workers <число>` — количество потоков / процессов / корутин.

## Задача 2 — параллельный парсинг

```bash
cd lab2/task2
python3 parse_threading.py
python3 parse_multiprocessing.py --workers 4
python3 parse_async.py
```

Все три скрипта используют один и тот же список URL из `urls.py` и один
и тот же движок БД из `db.py`. Таблица `parsed_page` создаётся
автоматически при первом запуске.

Проверить сохранённые записи:

```bash
sqlite3 ../../bookcrossing.db \
  "SELECT id, approach, url, title FROM parsed_page ORDER BY parsed_at DESC LIMIT 20;"
```
