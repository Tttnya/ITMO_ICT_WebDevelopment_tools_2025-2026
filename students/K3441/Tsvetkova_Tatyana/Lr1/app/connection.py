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
