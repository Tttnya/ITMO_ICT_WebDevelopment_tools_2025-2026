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
