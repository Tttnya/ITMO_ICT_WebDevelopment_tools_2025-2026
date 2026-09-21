# Миграции (Alembic)

Миграции сгенерированы через `--autogenerate` от `SQLModel.metadata`. Alembic
подхватывает URL из того же `.env`, что и приложение, — дублирования
конфигурации нет.

## `alembic.ini`

```ini title="alembic.ini"
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic
...
```

`sqlalchemy.url` пустой намеренно — реальное значение подставляется в
`env.py` из `.env`.

## `migrations/env.py`

```python title="migrations/env.py" linenums="1"
"""Alembic environment: URL берётся из .env, target_metadata — SQLModel.metadata."""
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Импортируем модели, чтобы SQLModel.metadata знал о таблицах.
from app import models  # noqa: F401

load_dotenv()

config = context.config

# Подставляем URL из окружения.
db_url = os.getenv("DB_ADMIN")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## `script.py.mako`

В шаблон миграций добавлен импорт `sqlmodel`, как требуется практикой 1.3:

```python title="migrations/script.py.mako"
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
${imports if imports else ""}
...
```

## Как применять

```bash
alembic revision --autogenerate -m "init schema"
alembic upgrade head
```

Первая команда сформировала файл `migrations/versions/…_init_schema.py`,
в котором Alembic описал `op.create_table(...)` для каждой из шести таблиц.
Вторая команда его применила.

!!! tip "Autogenerate log"
    ```
    INFO  [alembic.autogenerate.compare] Detected added table 'book'
    INFO  [alembic.autogenerate.compare] Detected added table 'genre'
    INFO  [alembic.autogenerate.compare] Detected added table 'user'
    INFO  [alembic.autogenerate.compare] Detected added index 'ix_user_email' on '('email',)'
    INFO  [alembic.autogenerate.compare] Detected added index 'ix_user_username' on '('username',)'
    INFO  [alembic.autogenerate.compare] Detected added table 'book_genre_link'
    INFO  [alembic.autogenerate.compare] Detected added table 'book_ownership'
    INFO  [alembic.autogenerate.compare] Detected added table 'exchange_request'
    ```
