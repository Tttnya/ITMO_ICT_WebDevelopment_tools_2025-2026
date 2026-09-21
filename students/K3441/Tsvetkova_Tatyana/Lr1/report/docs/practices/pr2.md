# Практика 1.2 — SQLModel, PostgreSQL, ORM

**Ссылка на репозиторий:** [Ссылка на коммит/ветку/папку](https://github.com/Tttnya/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/main/students/K3441/Tsvetkova_Tatyana/Lr1)

## Что сделано

* Установлены `sqlmodel`, `psycopg2-binary`.
* Создан модуль подключения `app/connection.py` с `engine`, `get_session`,
  `init_db` (см. [Подключение к БД](../report/connection.md)).
* Модели переведены с чистого Pydantic на SQLModel (`table=True`,
  `Field(foreign_key=...)`, `Relationship`).
* Реализована ассоциативная сущность `BookGenreLink` с полем `relevance`
  для M2M `Book ↔ Genre` (см. [Модель данных](../report/models.md)).
* Обновлены все CRUD-эндпоинты: теперь работают с реальной БД через
  `session=Depends(get_session)` и `session.exec(select(...))`.
* Реализованы GET-запросы с вложенными объектами через `response_model`:
    * `GET /books/{id}` возвращает книгу с вложенным списком жанров.
    * `GET /genres/{id}` возвращает жанр с вложенным списком книг
      (обратная M2M).
    * `GET /users/{id}` возвращает пользователя с вложенной библиотекой
      (one-to-many).

## Ключевой момент — M2M с полем в ассоциации

```python
class BookGenreLinkBase(SQLModel):
    relevance: int = Field(default=5, ge=1, le=10)

class BookGenreLink(BookGenreLinkBase, table=True):
    __tablename__ = "book_genre_link"
    book_id: Optional[int] = Field(default=None, foreign_key="book.id", primary_key=True)
    genre_id: Optional[int] = Field(default=None, foreign_key="genre.id", primary_key=True)

class Book(BookDefault, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    genres: List[Genre] = Relationship(back_populates="books", link_model=BookGenreLink)
```

## Пример обновлённого эндпоинта

```python
@router.post("/", response_model=BookRead, status_code=201)
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
            session.add(BookGenreLink(book_id=book.id, genre_id=gid, relevance=5))
        session.commit()
        session.refresh(book)
    return book
```

## Пример вложенного ответа (M2M в обе стороны)

`GET /books/1` →

```json
{
  "id": 1,
  "title": "Dune",
  "author": "Frank Herbert",
  "genres": [
    {"id": 1, "name": "Sci-Fi"},
    {"id": 2, "name": "Fantasy"}
  ]
}
```

`GET /genres/2` →

```json
{
  "id": 2,
  "name": "Fantasy",
  "books": [
    {"id": 1, "title": "Dune", "author": "Frank Herbert"},
    {"id": 2, "title": "The Hobbit", "author": "J.R.R. Tolkien"}
  ]
}
```
