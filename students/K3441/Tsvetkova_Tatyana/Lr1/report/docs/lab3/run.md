# Запуск ЛР3

## Одной командой

```bash
cd bookcrossing
docker compose up --build
```

Поднимутся 5 контейнеров: `db`, `redis`, `api` (`:8000`), `parser`
(`:8001`), `worker`. Проверить статус:

```bash
docker compose ps
```

## Документация API

* `http://localhost:8000/docs` — основное приложение (ЛР1 + `parsing`)
* `http://localhost:8001/docs` — отдельный сервис-парсер

Оба — Swagger UI с кнопкой **Try it out**, эндпоинты `/parsing/*` уже
содержат пример URL в теле запроса — тестировать можно вообще без
терминала, только кликами.

## Проверка через curl

```bash
# Подзадача 2 — синхронный вызов
curl -X POST http://localhost:8000/parsing/sync \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.python.org"}'

# Подзадача 3 — через очередь
curl -X POST http://localhost:8000/parsing/async \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org/3/"}'
# скопировать task_id из ответа
curl http://localhost:8000/parsing/async/<task_id>
```

## Проверка данных в базе

```bash
docker compose exec db psql -U postgres -d bookcrossing_db \
  -c "select id, url, title, approach, created_at from parsed_page order by id;"
```

## Логи

```bash
docker compose logs api --tail=50
docker compose logs worker --tail=50
docker compose logs parser --tail=50
```

## Остановка

```bash
docker compose down        # оставить данные в volume
docker compose down -v     # + стереть базу (чистый старт)
```
