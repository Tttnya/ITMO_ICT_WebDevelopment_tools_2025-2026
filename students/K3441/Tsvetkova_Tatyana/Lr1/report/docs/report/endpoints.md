# API-эндпоинты

Всего **34 эндпоинта** в шести доменных пакетах. Полная интерактивная
документация доступна на `http://127.0.0.1:8000/docs` (Swagger UI).

| Метод   | Путь                                     | Раздел     | Аутентификация |
|---------|------------------------------------------|------------|:-:|
| GET     | `/`                                      | root       |  |
| POST    | `/auth/register`                         | auth       |  |
| POST    | `/auth/login`                            | auth       |  |
| GET     | `/auth/me`                               | auth       | ✓ |
| POST    | `/auth/change-password`                  | auth       | ✓ |
| GET     | `/users/`                                | users      |  |
| GET     | `/users/{user_id}`                       | users      |  |
| PATCH   | `/users/me`                              | users      | ✓ |
| DELETE  | `/users/me`                              | users      | ✓ |
| GET     | `/books/`                                | books      |  |
| POST    | `/books/`                                | books      | ✓ |
| GET     | `/books/{book_id}`                       | books      |  |
| PATCH   | `/books/{book_id}`                       | books      | ✓ |
| DELETE  | `/books/{book_id}`                       | books      | ✓ |
| POST    | `/books/{book_id}/genres`                | books      | ✓ |
| DELETE  | `/books/{book_id}/genres/{genre_id}`     | books      | ✓ |
| GET     | `/genres/`                               | genres     |  |
| POST    | `/genres/`                               | genres     | ✓ |
| GET     | `/genres/{genre_id}`                     | genres     |  |
| PATCH   | `/genres/{genre_id}`                     | genres     | ✓ |
| DELETE  | `/genres/{genre_id}`                     | genres     | ✓ |
| GET     | `/library/me`                            | library    | ✓ |
| GET     | `/library/users/{user_id}`               | library    |  |
| GET     | `/library/search`                        | library    |  |
| POST    | `/library/`                              | library    | ✓ |
| PATCH   | `/library/{ownership_id}`                | library    | ✓ |
| DELETE  | `/library/{ownership_id}`                | library    | ✓ |
| POST    | `/exchanges/`                            | exchanges  | ✓ |
| GET     | `/exchanges/incoming`                    | exchanges  | ✓ |
| GET     | `/exchanges/outgoing`                    | exchanges  | ✓ |
| GET     | `/exchanges/{exchange_id}`               | exchanges  | ✓ |
| POST    | `/exchanges/{exchange_id}/accept`        | exchanges  | ✓ |
| POST    | `/exchanges/{exchange_id}/decline`       | exchanges  | ✓ |
| POST    | `/exchanges/{exchange_id}/cancel`        | exchanges  | ✓ |
| POST    | `/exchanges/{exchange_id}/complete`      | exchanges  | ✓ |

---

## `app/users/router.py`

```python title="app/users/router.py" linenums="1"
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth.dependencies import get_current_user
from ..connection import get_session
from ..models import (
    Book,
    BookOwnership,
    BookOwnershipDefault,
    User,
    UserDefault,
)


router = APIRouter(prefix="/users", tags=["users"])


class UserPublic(UserDefault):
    id: int
    is_active: bool


class OwnershipWithBook(BookOwnershipDefault):
    id: int
    book: Optional[Book] = None


class UserWithLibrary(UserPublic):
    library: List[OwnershipWithBook] = []


@router.get("/", response_model=List[UserPublic])
def list_users(
    session: Session = Depends(get_session),
    city: Optional[str] = None,
) -> List[User]:
    query = select(User)
    if city:
        query = query.where(User.city == city)
    return session.exec(query).all()


@router.get("/{user_id}", response_model=UserWithLibrary)
def get_user(user_id: int, session: Session = Depends(get_session)) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UserDefault,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> User:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(current_user, key, value)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    session.delete(current_user)
    session.commit()
    return None
```

## `app/books/router.py`

Реализует управление связями `Book ↔ Genre` через ассоциативную сущность.
`GET /books/{id}` возвращает книгу с вложенным списком жанров.

```python title="app/books/router.py" linenums="1"
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth.dependencies import get_current_user
from ..connection import get_session
from ..models import (
    Book,
    BookDefault,
    BookGenreLink,
    BookGenreLinkBase,
    Genre,
    GenreDefault,
    User,
)


router = APIRouter(prefix="/books", tags=["books"])


class GenreLinkedOut(GenreDefault):
    id: int
    relevance: int


class BookRead(BookDefault):
    id: int
    genres: List[Genre] = []


class BookCreate(BookDefault):
    genre_ids: Optional[List[int]] = None


class GenreAttachRequest(BookGenreLinkBase):
    genre_id: int


@router.get("/", response_model=List[BookRead])
def list_books(
    session: Session = Depends(get_session),
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre_id: Optional[int] = None,
) -> List[Book]:
    query = select(Book)
    if title:
        query = query.where(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.where(Book.author.ilike(f"%{author}%"))
    if genre_id:
        query = query.join(BookGenreLink).where(BookGenreLink.genre_id == genre_id)
    return session.exec(query).all()


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, session: Session = Depends(get_session)) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Book:
    book = Book.model_validate(payload.model_dump(exclude={"genre_ids"}))
    session.add(book)
    session.commit()
    session.refresh(book)
    if payload.genre_ids:
        for gid in payload.genre_ids:
            genre = session.get(Genre, gid)
            if genre is None:
                continue
            session.add(BookGenreLink(book_id=book.id, genre_id=gid, relevance=5))
        session.commit()
        session.refresh(book)
    return book


@router.patch("/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    payload: BookDefault,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(book, key, value)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    session.delete(book)
    session.commit()
    return None


@router.post("/{book_id}/genres", response_model=BookRead)
def attach_genre(
    book_id: int,
    payload: GenreAttachRequest,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    genre = session.get(Genre, payload.genre_id)
    if genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    existing = session.get(BookGenreLink, (book_id, payload.genre_id))
    if existing is not None:
        existing.relevance = payload.relevance
        session.add(existing)
    else:
        session.add(
            BookGenreLink(
                book_id=book_id,
                genre_id=payload.genre_id,
                relevance=payload.relevance,
            )
        )
    session.commit()
    session.refresh(book)
    return book


@router.delete("/{book_id}/genres/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_genre(
    book_id: int,
    genre_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    link = session.get(BookGenreLink, (book_id, genre_id))
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    session.delete(link)
    session.commit()
    return None
```

## `app/genres/router.py`

`GET /genres/{id}` возвращает жанр с вложенным списком книг — обратная
сторона M2M.

```python title="app/genres/router.py" linenums="1"
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth.dependencies import get_current_user
from ..connection import get_session
from ..models import Book, Genre, GenreDefault, User


router = APIRouter(prefix="/genres", tags=["genres"])


class GenreRead(GenreDefault):
    id: int


class GenreWithBooks(GenreRead):
    books: List[Book] = []


@router.get("/", response_model=List[GenreRead])
def list_genres(session: Session = Depends(get_session)) -> List[Genre]:
    return session.exec(select(Genre)).all()


@router.get("/{genre_id}", response_model=GenreWithBooks)
def get_genre(genre_id: int, session: Session = Depends(get_session)) -> Genre:
    genre = session.get(Genre, genre_id)
    if genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre


@router.post("/", response_model=GenreRead, status_code=status.HTTP_201_CREATED)
def create_genre(
    payload: GenreDefault,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Genre:
    genre = Genre.model_validate(payload)
    session.add(genre)
    session.commit()
    session.refresh(genre)
    return genre


@router.patch("/{genre_id}", response_model=GenreRead)
def update_genre(
    genre_id: int,
    payload: GenreDefault,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Genre:
    genre = session.get(Genre, genre_id)
    if genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(genre, key, value)
    session.add(genre)
    session.commit()
    session.refresh(genre)
    return genre


@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_genre(
    genre_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    genre = session.get(Genre, genre_id)
    if genre is None:
        raise HTTPException(status_code=404, detail="Genre not found")
    session.delete(genre)
    session.commit()
    return None
```

## `app/library/router.py`

Управление экземплярами книг у пользователя (`BookOwnership`) — реализация
one-to-many связей `User → BookOwnership` и `Book → BookOwnership`.

```python title="app/library/router.py" linenums="1"
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth.dependencies import get_current_user
from ..connection import get_session
from ..models import Book, BookOwnership, BookOwnershipDefault, User


router = APIRouter(prefix="/library", tags=["library"])


class OwnershipRead(BookOwnershipDefault):
    id: int
    owner_id: int
    book: Optional[Book] = None


@router.get("/me", response_model=List[OwnershipRead])
def list_my_library(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[BookOwnership]:
    return session.exec(
        select(BookOwnership).where(BookOwnership.owner_id == current_user.id)
    ).all()


@router.get("/users/{user_id}", response_model=List[OwnershipRead])
def list_user_library(
    user_id: int,
    session: Session = Depends(get_session),
) -> List[BookOwnership]:
    return session.exec(
        select(BookOwnership).where(BookOwnership.owner_id == user_id)
    ).all()


@router.get(
    "/search",
    response_model=List[OwnershipRead],
    summary="Найти доступные для обмена экземпляры книги",
)
def search_available(
    session: Session = Depends(get_session),
    book_id: Optional[int] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    city: Optional[str] = None,
) -> List[BookOwnership]:
    query = (
        select(BookOwnership)
        .join(Book, Book.id == BookOwnership.book_id)
        .join(User, User.id == BookOwnership.owner_id)
        .where(BookOwnership.is_available == True)  # noqa: E712
    )
    if book_id is not None:
        query = query.where(BookOwnership.book_id == book_id)
    if title:
        query = query.where(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.where(Book.author.ilike(f"%{author}%"))
    if city:
        query = query.where(User.city == city)
    return session.exec(query).all()


@router.post(
    "/",
    response_model=OwnershipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить экземпляр книги в свою библиотеку",
)
def add_to_library(
    payload: BookOwnershipDefault,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BookOwnership:
    book = session.get(Book, payload.book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    ownership = BookOwnership(
        **payload.model_dump(),
        owner_id=current_user.id,
    )
    session.add(ownership)
    session.commit()
    session.refresh(ownership)
    return ownership


@router.patch("/{ownership_id}", response_model=OwnershipRead)
def update_ownership(
    ownership_id: int,
    payload: BookOwnershipDefault,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BookOwnership:
    ownership = session.get(BookOwnership, ownership_id)
    if ownership is None:
        raise HTTPException(status_code=404, detail="Ownership not found")
    if ownership.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your book")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(ownership, key, value)
    session.add(ownership)
    session.commit()
    session.refresh(ownership)
    return ownership


@router.delete("/{ownership_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_library(
    ownership_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    ownership = session.get(BookOwnership, ownership_id)
    if ownership is None:
        raise HTTPException(status_code=404, detail="Ownership not found")
    if ownership.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your book")
    session.delete(ownership)
    session.commit()
    return None
```

## `app/exchanges/router.py`

Полный жизненный цикл запроса на обмен: `pending → accepted → completed`
(или `declined` / `cancelled`).

```python title="app/exchanges/router.py" linenums="1"
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..auth.dependencies import get_current_user
from ..connection import get_session
from ..models import (
    BookOwnership,
    ExchangeRequest,
    ExchangeRequestDefault,
    ExchangeStatus,
    User,
)


router = APIRouter(prefix="/exchanges", tags=["exchanges"])


class ExchangeRead(ExchangeRequestDefault):
    id: int
    requester_id: int
    owner_id: int
    status: ExchangeStatus
    created_at: datetime
    updated_at: datetime


class ExchangeDetailed(ExchangeRead):
    offered: Optional[BookOwnership] = None
    requested: Optional[BookOwnership] = None


class ExchangeCreate(ExchangeRequestDefault):
    pass


@router.post(
    "/",
    response_model=ExchangeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить запрос на обмен",
)
def create_exchange(
    payload: ExchangeCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    offered = session.get(BookOwnership, payload.offered_ownership_id)
    requested = session.get(BookOwnership, payload.requested_ownership_id)
    if offered is None or requested is None:
        raise HTTPException(status_code=404, detail="Ownership record not found")
    if offered.owner_id != current_user.id:
        raise HTTPException(
            status_code=400, detail="Offered book does not belong to you"
        )
    if requested.owner_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Requested book belongs to you already"
        )
    if not offered.is_available or not requested.is_available:
        raise HTTPException(
            status_code=400, detail="One of the books is not available for exchange"
        )
    exchange = ExchangeRequest(
        offered_ownership_id=payload.offered_ownership_id,
        requested_ownership_id=payload.requested_ownership_id,
        message=payload.message,
        requester_id=current_user.id,
        owner_id=requested.owner_id,
    )
    session.add(exchange)
    session.commit()
    session.refresh(exchange)
    return exchange


@router.get("/incoming", response_model=List[ExchangeDetailed])
def list_incoming(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[ExchangeStatus] = None,
) -> List[ExchangeDetailed]:
    query = select(ExchangeRequest).where(ExchangeRequest.owner_id == current_user.id)
    if status_filter is not None:
        query = query.where(ExchangeRequest.status == status_filter)
    return [_hydrate(session, ex) for ex in session.exec(query).all()]


@router.get("/outgoing", response_model=List[ExchangeDetailed])
def list_outgoing(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[ExchangeStatus] = None,
) -> List[ExchangeDetailed]:
    query = select(ExchangeRequest).where(
        ExchangeRequest.requester_id == current_user.id
    )
    if status_filter is not None:
        query = query.where(ExchangeRequest.status == status_filter)
    return [_hydrate(session, ex) for ex in session.exec(query).all()]


@router.get("/{exchange_id}", response_model=ExchangeDetailed)
def get_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeDetailed:
    ex = session.get(ExchangeRequest, exchange_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Exchange not found")
    if current_user.id not in (ex.requester_id, ex.owner_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    return _hydrate(session, ex)


@router.post("/{exchange_id}/accept", response_model=ExchangeRead)
def accept_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    ex = _get_owned(session, exchange_id, current_user, participant="owner")
    if ex.status != ExchangeStatus.pending:
        raise HTTPException(status_code=400, detail="Exchange is not pending")
    ex.status = ExchangeStatus.accepted
    ex.updated_at = datetime.utcnow()
    for oid in (ex.offered_ownership_id, ex.requested_ownership_id):
        ownership = session.get(BookOwnership, oid)
        if ownership is not None:
            ownership.is_available = False
            session.add(ownership)
    session.add(ex)
    session.commit()
    session.refresh(ex)
    return ex


@router.post("/{exchange_id}/decline", response_model=ExchangeRead)
def decline_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    ex = _get_owned(session, exchange_id, current_user, participant="owner")
    if ex.status != ExchangeStatus.pending:
        raise HTTPException(status_code=400, detail="Exchange is not pending")
    ex.status = ExchangeStatus.declined
    ex.updated_at = datetime.utcnow()
    session.add(ex)
    session.commit()
    session.refresh(ex)
    return ex


@router.post("/{exchange_id}/cancel", response_model=ExchangeRead)
def cancel_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    ex = _get_owned(session, exchange_id, current_user, participant="requester")
    if ex.status not in (ExchangeStatus.pending, ExchangeStatus.accepted):
        raise HTTPException(status_code=400, detail="Cannot cancel finalized exchange")
    ex.status = ExchangeStatus.cancelled
    ex.updated_at = datetime.utcnow()
    session.add(ex)
    session.commit()
    session.refresh(ex)
    return ex


@router.post("/{exchange_id}/complete", response_model=ExchangeRead)
def complete_exchange(
    exchange_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ExchangeRequest:
    ex = session.get(ExchangeRequest, exchange_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Exchange not found")
    if current_user.id not in (ex.requester_id, ex.owner_id):
        raise HTTPException(status_code=403, detail="Not a participant")
    if ex.status != ExchangeStatus.accepted:
        raise HTTPException(status_code=400, detail="Exchange is not accepted yet")
    ex.status = ExchangeStatus.completed
    ex.updated_at = datetime.utcnow()
    session.add(ex)
    session.commit()
    session.refresh(ex)
    return ex


def _get_owned(
    session: Session,
    exchange_id: int,
    user: User,
    participant: str,
) -> ExchangeRequest:
    ex = session.get(ExchangeRequest, exchange_id)
    if ex is None:
        raise HTTPException(status_code=404, detail="Exchange not found")
    expected_id = ex.owner_id if participant == "owner" else ex.requester_id
    if expected_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this participant")
    return ex


def _hydrate(session: Session, ex: ExchangeRequest) -> ExchangeDetailed:
    return ExchangeDetailed(
        **ex.model_dump(),
        offered=session.get(BookOwnership, ex.offered_ownership_id),
        requested=session.get(BookOwnership, ex.requested_ownership_id),
    )
```
