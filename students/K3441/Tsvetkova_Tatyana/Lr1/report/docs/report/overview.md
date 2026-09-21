# Обзор проекта

## Структура папок

```
bookcrossing/
├── app/
│   ├── __init__.py
│   ├── main.py                  # точка входа FastAPI, подключение роутеров
│   ├── connection.py            # engine, get_session, init_db (читает .env)
│   ├── models.py                # SQLModel-модели всех 6 таблиц
│   ├── auth/                    # регистрация, логин, JWT, guard
│   │   ├── router.py
│   │   ├── utils.py             # bcrypt + PyJWT
│   │   └── dependencies.py      # ручная проверка JWT
│   ├── users/router.py          # эндпоинты пользователей
│   ├── books/router.py          # каталог книг + M2M с жанрами
│   ├── genres/router.py         # CRUD жанров
│   ├── library/router.py        # библиотека пользователя (BookOwnership)
│   └── exchanges/router.py      # запросы на обмен
├── migrations/                  # Alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/…_init_schema.py
├── alembic.ini
├── requirements.txt
├── .env                         # DB_ADMIN, JWT_SECRET, …
├── .gitignore
└── README.md
```

## Разделение по бизнес-логике

Каждая предметная область живёт в собственном пакете `app/<domain>/`, что
удовлетворяет требованию **«оформленная файловая структура с разделением
кода на отдельные файлы и папки»**.

| Пакет           | Ответственность                                          |
|-----------------|----------------------------------------------------------|
| `app.auth`      | регистрация, логин, JWT, `get_current_user` dependency  |
| `app.users`     | публичные эндпоинты пользователей                        |
| `app.books`     | каталог книг + управление связями с жанрами (M2M)        |
| `app.genres`    | справочник жанров                                        |
| `app.library`   | экземпляры книг в личных библиотеках + поиск             |
| `app.exchanges` | запросы на обмен и их жизненный цикл                     |

Общее лежит на верхнем уровне:

* `app.models` — все SQLModel-таблицы (единый `SQLModel.metadata`
  используется и рантаймом, и Alembic).
* `app.connection` — engine, генератор сессий, `init_db`.
* `app.main` — сборка `FastAPI`, `on_startup`, подключение всех роутеров.

## Точка входа

```python title="app/main.py"
from fastapi import FastAPI

from .auth.router import router as auth_router
from .books.router import router as books_router
from .connection import init_db
from .exchanges.router import router as exchanges_router
from .genres.router import router as genres_router
from .library.router import router as library_router
from .users.router import router as users_router


app = FastAPI(
    title="Bookcrossing API",
    description=(
        "Серверная часть веб-приложения для буккроссинга. "
        "Пользователи регистрируются, добавляют книги в свою библиотеку, "
        "ищут книги других пользователей и обмениваются ими."
    ),
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", tags=["root"])
def root() -> dict:
    return {
        "service": "bookcrossing",
        "status": "ok",
        "docs": "/docs",
    }


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(books_router)
app.include_router(genres_router)
app.include_router(library_router)
app.include_router(exchanges_router)
```
