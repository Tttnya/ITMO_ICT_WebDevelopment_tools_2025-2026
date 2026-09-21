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
