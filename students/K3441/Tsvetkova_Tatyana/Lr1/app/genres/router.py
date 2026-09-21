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
