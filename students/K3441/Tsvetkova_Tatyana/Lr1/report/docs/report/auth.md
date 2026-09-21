# Авторизация и JWT

## Разграничение обязанностей

Согласно требованию задания на 15 баллов, **аутентификация по JWT-токену
реализована вручную**, без использования сторонних библиотек-обёрток.
Хэширование паролей (bcrypt) и создание JWT (PyJWT) — по условию разрешены.

* `app/auth/utils.py` — хэширование bcrypt + создание/декодирование JWT.
* `app/auth/dependencies.py` — **ручной guard**: парсинг заголовка, проверка
  подписи и `exp`, извлечение пользователя из БД.
* `app/auth/router.py` — эндпоинты `register`, `login`, `me`, `change-password`.

## `app/auth/utils.py`

```python title="app/auth/utils.py" linenums="1"
"""Хэширование паролей и создание JWT-токенов.

Согласно заданию: сама аутентификация (парсинг заголовка Authorization,
валидация и извлечение пользователя) реализована вручную в dependencies.py.
Хэширование паролей и подпись JWT — разрешены сторонние библиотеки.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET: str = os.getenv("JWT_SECRET", "insecure-dev-secret")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: int, extra: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(tz=timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRE_MINUTES)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
```

## `app/auth/dependencies.py` — ручной JWT-guard

Ключевой файл, реализующий требование методички:
*«п.3 [Аутентификация по JWT-токену] реализовать вручную, без использования
сторонних библиотек»*.

```python title="app/auth/dependencies.py" linenums="1"
"""Ручная реализация JWT-аутентификации (без готовых библиотек-обёрток).

Извлекаем токен из заголовка `Authorization: Bearer <token>`, валидируем его
через utils.decode_token и достаём пользователя из БД.
"""
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from ..connection import get_session
from ..models import User
from .utils import decode_token


def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1]


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    token = _extract_bearer(authorization)
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject in token",
        )

    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user
```

Функция `get_current_user` подключается к любому защищённому эндпоинту
через `Depends(get_current_user)` и возвращает валидного `User` либо
`HTTPException 401`.

## `app/auth/router.py` — эндпоинты

```python title="app/auth/router.py" linenums="1"
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..connection import get_session
from ..models import User, UserDefault
from .dependencies import get_current_user
from .utils import create_access_token, hash_password, verify_password
from pydantic import BaseModel, EmailStr, Field


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(UserDefault):
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


class UserPublic(UserDefault):
    id: int
    is_active: bool


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: Session = Depends(get_session)) -> User:
    exists = session.exec(
        select(User).where(
            (User.username == payload.username) | (User.email == payload.email)
        )
    ).first()
    if exists is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this username or email already exists",
        )
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        city=payload.city,
        bio=payload.bio,
        hashed_password=hash_password(payload.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    user = session.exec(select(User).where(User.username == payload.username)).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    token = create_access_token(user_id=user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    current_user.hashed_password = hash_password(payload.new_password)
    session.add(current_user)
    session.commit()
    return None
```

## Проверка вживую

```bash
# Регистрация
curl -X POST http://127.0.0.1:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"a@b.io","password":"secret123"}'

# Логин
curl -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"secret123"}'
# → {"access_token": "eyJhbGciOi…", "token_type": "bearer"}

# Защищённый эндпоинт
curl http://127.0.0.1:8000/auth/me \
  -H 'Authorization: Bearer eyJhbGciOi…'
# → {"username":"alice","email":"a@b.io",…}

# Без токена
curl http://127.0.0.1:8000/auth/me
# → 401 {"detail":"Authorization header is missing"}
```
