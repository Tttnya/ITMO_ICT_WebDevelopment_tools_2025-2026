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
