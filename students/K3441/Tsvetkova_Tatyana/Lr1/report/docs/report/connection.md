# Подключение к БД

URL базы вынесен в `.env` и загружается через `python-dotenv`. Внутри
приложения нет ни одного захардкоженного пароля или адреса.

## `app/connection.py`

```python title="app/connection.py" linenums="1"
import os
from typing import Generator

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

db_url = os.getenv("DB_ADMIN", "postgresql://postgres:123@localhost/bookcrossing_db")
# SQLite требует отключить проверку одного треда при работе с FastAPI/uvicorn.
_engine_kwargs = {"echo": True}
if db_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(db_url, **_engine_kwargs)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

* `engine` — единый на приложение объект SQLAlchemy, отвечает за пул
  соединений и диалект. `echo=True` печатает SQL в консоль — удобно при
  разработке.
* `init_db()` вызывается на старте (`@app.on_event("startup")`) и создаёт
  таблицы, если их нет.
* `get_session()` — генератор, отдающий `Session`. Пробрасывается в
  эндпоинты через `Depends(get_session)`.

## `.env`

```env title=".env"
DB_ADMIN=postgresql://postgres:123@localhost/bookcrossing_db
JWT_SECRET=change-me-to-a-long-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

!!! warning "Файл не коммитим"
    `.env` исключён из индексации git через `.gitignore` (правило `*.env`),
    как рекомендует практика 1.3.

## `.gitignore`

```gitignore title=".gitignore"
*.env
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/
.idea/
.vscode/
*.sqlite3
*.db
.DS_Store
```
