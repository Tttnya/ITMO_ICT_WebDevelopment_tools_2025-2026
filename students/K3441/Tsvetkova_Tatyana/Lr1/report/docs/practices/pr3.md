# Практика 1.3 — Alembic, .env, .gitignore, структура проекта

**Ссылка на репозиторий:** [Ссылка на коммит/ветку/папку](https://github.com/Tttnya/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/main/students/K3441/Tsvetkova_Tatyana/Lr1)

## Что сделано

* Установлен `alembic`, инициализирован каталог миграций
  (`alembic init migrations`).
* Настроен `migrations/env.py`:
    * `target_metadata = SQLModel.metadata`,
    * URL БД подставляется из `.env` через `python-dotenv`
      (см. [Миграции](../report/migrations.md)).
* В `migrations/script.py.mako` добавлен импорт `sqlmodel`
  (нужен для типов `sqlmodel.sql.sqltypes.AutoString` в
  автосгенерированных миграциях).
* Создана и применена автосгенерированная миграция:
  `alembic revision --autogenerate -m "init schema"` → `alembic upgrade head`.
* Реализован файл `.env` с чувствительными данными.
* Реализован `.gitignore`, исключающий `*.env`, `__pycache__`, `.venv` и т. п.
* Финальная структура проекта разделена на пакеты по бизнес-логике
  (см. [Обзор](../report/overview.md)).

## Передача URL БД в `alembic.ini` через `.env`

По заданию требуется разобраться, **как передать в `alembic.ini` URL из
`.env`, а не хардкодить его**. Реализовано следующим образом:

1. В `alembic.ini` строка `sqlalchemy.url =` оставлена **пустой**.
2. В `migrations/env.py` до `fileConfig()` вызывается `load_dotenv()` и
   значение из `os.getenv("DB_ADMIN")` подставляется через
   `config.set_main_option("sqlalchemy.url", db_url)`.
3. Далее Alembic использует уже подставленное значение при создании engine.

```python title="migrations/env.py"
load_dotenv()
config = context.config
db_url = os.getenv("DB_ADMIN")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)
```

Это позволяет держать один и тот же URL и в приложении, и в Alembic, не
дублируя его.

## Итоговая структура проекта

```
bookcrossing/
├── app/                # весь код приложения разбит на пакеты по домену
│   ├── auth/
│   ├── users/
│   ├── books/
│   ├── genres/
│   ├── library/
│   ├── exchanges/
│   ├── main.py
│   ├── connection.py
│   └── models.py
├── migrations/         # Alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── requirements.txt
├── .env                # НЕ индексируется git
├── .gitignore
└── README.md
```
