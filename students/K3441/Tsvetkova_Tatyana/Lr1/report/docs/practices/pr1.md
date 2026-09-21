# Практика 1.1 — Базовое приложение на FastAPI

**Ссылка на репозиторий:** [Ссылка на коммит/ветку/папку](https://github.com/Tttnya/ITMO_ICT_WebDevelopment_tools_2025-2026/tree/main/students/K3441/Tsvetkova_Tatyana/Lr1)

## Что сделано

* Создан проект FastAPI с виртуальным окружением.
* Реализована временная БД `temp_bd` с двумя-тремя записями книг
  (главная сущность — `Book`) с одиночным вложенным объектом (`Author`) и
  списком объектов (`Genre`).
* Реализованы базовые CRUD-эндпоинты для главной сущности.
* Добавлены Pydantic-модели и аннотации типов.
* Реализованы модели и API для вложенного объекта (`Author`).

## Пример временной БД

```python
temp_bd = [
    {
        "id": 1,
        "title": "Dune",
        "author": {"id": 1, "name": "Frank Herbert"},
        "genres": [{"id": 1, "name": "Sci-Fi"}],
        "year": 1965,
    },
    {
        "id": 2,
        "title": "The Hobbit",
        "author": {"id": 2, "name": "J.R.R. Tolkien"},
        "genres": [{"id": 2, "name": "Fantasy"}],
        "year": 1937,
    },
]
```

## Реализованные CRUD-методы

* `GET /books_list` — список книг
* `GET /book/{book_id}` — одна книга
* `POST /book` — добавить книгу
* `PUT /book/{book_id}` — обновить книгу
* `DELETE /book/delete{book_id}` — удалить книгу
* Аналогичный CRUD для `Author`

## Финальные Pydantic-модели (см. также [Модель данных](../report/models.md))

```python
from typing import List, Optional
from pydantic import BaseModel

class Author(BaseModel):
    id: int
    name: str

class Genre(BaseModel):
    id: int
    name: str

class Book(BaseModel):
    id: int
    title: str
    author: Author
    genres: Optional[List[Genre]] = []
    year: Optional[int] = None
```
