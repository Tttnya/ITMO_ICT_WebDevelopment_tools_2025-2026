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
