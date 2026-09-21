from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class BookCondition(str, Enum):
    """Состояние экземпляра книги, которым делится пользователь."""

    new = "new"
    good = "good"
    used = "used"
    worn = "worn"


class ExchangeStatus(str, Enum):
    """Жизненный цикл запроса на обмен."""

    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"
    completed = "completed"


# ---------------------------------------------------------------------------
# Ассоциативная сущность: many-to-many между Book и Genre.
# Помимо ссылок содержит поле relevance — насколько жанр характерен для книги.
# ---------------------------------------------------------------------------
class BookGenreLinkBase(SQLModel):
    relevance: int = Field(default=5, ge=1, le=10)


class BookGenreLink(BookGenreLinkBase, table=True):
    __tablename__ = "book_genre_link"

    book_id: Optional[int] = Field(
        default=None, foreign_key="book.id", primary_key=True
    )
    genre_id: Optional[int] = Field(
        default=None, foreign_key="genre.id", primary_key=True
    )


# ---------------------------------------------------------------------------
# Жанр
# ---------------------------------------------------------------------------
class GenreDefault(SQLModel):
    name: str
    description: Optional[str] = None


class Genre(GenreDefault, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    books: List["Book"] = Relationship(
        back_populates="genres", link_model=BookGenreLink
    )


# ---------------------------------------------------------------------------
# Книга (глобальный каталог)
# ---------------------------------------------------------------------------
class BookDefault(SQLModel):
    title: str
    author: str
    year: Optional[int] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None


class Book(BookDefault, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    genres: List[Genre] = Relationship(
        back_populates="books", link_model=BookGenreLink
    )
    copies: List["BookOwnership"] = Relationship(
        back_populates="book",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )


# ---------------------------------------------------------------------------
# Пользователь
# ---------------------------------------------------------------------------
class UserDefault(SQLModel):
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None


class User(UserDefault, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    library: List["BookOwnership"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    outgoing_requests: List["ExchangeRequest"] = Relationship(
        back_populates="requester",
        sa_relationship_kwargs={
            "primaryjoin": "User.id == ExchangeRequest.requester_id",
            "foreign_keys": "[ExchangeRequest.requester_id]",
            "cascade": "all, delete",
        },
    )
    incoming_requests: List["ExchangeRequest"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={
            "primaryjoin": "User.id == ExchangeRequest.owner_id",
            "foreign_keys": "[ExchangeRequest.owner_id]",
            "cascade": "all, delete",
        },
    )


# ---------------------------------------------------------------------------
# BookOwnership — экземпляр книги в личной библиотеке пользователя.
# One-to-many:  User -> BookOwnership,  Book -> BookOwnership.
# ---------------------------------------------------------------------------
class BookOwnershipDefault(SQLModel):
    book_id: int = Field(foreign_key="book.id")
    condition: BookCondition = BookCondition.good
    notes: Optional[str] = None
    is_available: bool = True


class BookOwnership(BookOwnershipDefault, table=True):
    __tablename__ = "book_ownership"

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    owner: Optional[User] = Relationship(back_populates="library")
    book: Optional[Book] = Relationship(back_populates="copies")


# ---------------------------------------------------------------------------
# ExchangeRequest — запрос на обмен книгами.
# Ассоциативная сущность между двумя пользователями с полями, характеризующими связь.
# ---------------------------------------------------------------------------
class ExchangeRequestDefault(SQLModel):
    offered_ownership_id: int = Field(foreign_key="book_ownership.id")
    requested_ownership_id: int = Field(foreign_key="book_ownership.id")
    message: Optional[str] = None


class ExchangeRequest(ExchangeRequestDefault, table=True):
    __tablename__ = "exchange_request"

    id: Optional[int] = Field(default=None, primary_key=True)
    requester_id: int = Field(foreign_key="user.id")
    owner_id: int = Field(foreign_key="user.id")
    status: ExchangeStatus = ExchangeStatus.pending
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    requester: Optional[User] = Relationship(
        back_populates="outgoing_requests",
        sa_relationship_kwargs={
            "primaryjoin": "User.id == ExchangeRequest.requester_id",
            "foreign_keys": "[ExchangeRequest.requester_id]",
        },
    )
    owner: Optional[User] = Relationship(
        back_populates="incoming_requests",
        sa_relationship_kwargs={
            "primaryjoin": "User.id == ExchangeRequest.owner_id",
            "foreign_keys": "[ExchangeRequest.owner_id]",
        },
    )


# ---------------------------------------------------------------------------
# ParsedPage — результат работы парсера (лабораторная работа №3).
# approach отражает способ вызова: "sync-service" (через HTTP-сервис парсера)
# или "celery" (через очередь задач).
# ---------------------------------------------------------------------------
class ParsedPage(SQLModel, table=True):
    __tablename__ = "parsed_page"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    title: str
    approach: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
