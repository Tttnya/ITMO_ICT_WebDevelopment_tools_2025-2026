# Bookcrossing API (FastAPI + SQLModel + PostgreSQL + Alembic)

Лабораторная работа №1 (весенний семестр). Тема: **Разработка веб-приложения
для буккроссинга**.

Автор: **Цветкова Татьяна Александровна**.

## Модель данных

Всего **6 таблиц**, две связи `many-to-many`, несколько `one-to-many`,
ассоциативная сущность `BookGenreLink` содержит поле `relevance`,
характеризующее связь помимо ссылок на таблицы.

| Таблица              | Роль                                               |
|----------------------|----------------------------------------------------|
| `user`               | Пользователь платформы                             |
| `book`               | Глобальный каталог книг                            |
| `genre`              | Справочник жанров                                  |
| `book_genre_link`    | M2M `Book ↔ Genre` с полем `relevance`             |
| `book_ownership`     | Экземпляр книги в личной библиотеке пользователя   |
| `exchange_request`   | Запрос на обмен между двумя пользователями         |

Связи:

* `User 1-to-many BookOwnership` — библиотека пользователя;
* `Book 1-to-many BookOwnership` — экземпляры книги у разных пользователей;
* `User 1-to-many ExchangeRequest` (по `requester_id`, `owner_id`);
* `Book many-to-many Genre` через `BookGenreLink` (с полем `relevance`).

## Структура проекта

```
bookcrossing/
├── app/
│   ├── main.py            # точка входа FastAPI, подключение роутеров
│   ├── connection.py      # engine + Session + init_db, URL из .env
│   ├── models.py          # SQLModel-модели всех таблиц
│   ├── auth/              # регистрация, логин, JWT, смена пароля
│   ├── users/             # эндпоинты пользователей
│   ├── books/             # каталог книг + M2M с жанрами
│   ├── genres/            # CRUD жанров
│   ├── library/           # библиотека пользователя (BookOwnership)
│   └── exchanges/         # запросы на обмен
├── migrations/            # Alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── requirements.txt
├── .env                   # DB_ADMIN, JWT_SECRET, ...
└── .gitignore
```

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Создайте базу в PostgreSQL, укажите URL в `.env`:

```
DB_ADMIN=postgresql://postgres:123@localhost/bookcrossing_db
JWT_SECRET=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

Применить миграции:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

Запустить сервер:

```bash
uvicorn app.main:app --reload
```

Документация: <http://127.0.0.1:8000/docs>

## Аутентификация

* `POST /auth/register` — регистрация (пароли хэшируются `bcrypt`).
* `POST /auth/login` — выдача JWT (`PyJWT`, `HS256`).
* `GET  /auth/me` — информация о текущем пользователе.
* `POST /auth/change-password` — смена пароля.
* Проверка JWT в защищённых эндпоинтах реализована **вручную**
  в `app/auth/dependencies.py` (парсинг заголовка `Authorization: Bearer …`,
  валидация подписи и `exp`, извлечение пользователя из БД).

## Основные эндпоинты

* `GET/POST/PATCH/DELETE /books` — CRUD книг, `GET /books/{id}` возвращает
  жанры (вложенный объект).
* `POST /books/{id}/genres` — привязать жанр (с полем `relevance`),
  `DELETE /books/{id}/genres/{genre_id}` — отвязать.
* `GET /genres/{id}` — жанр с вложенным списком книг.
* `POST /library/` — добавить книгу в свою библиотеку.
* `GET /library/search` — поиск доступных для обмена экземпляров.
* `POST /exchanges/` — отправить запрос на обмен.
* `GET /exchanges/incoming`, `/outgoing` — списки запросов с вложенными
  экземплярами.
* `POST /exchanges/{id}/accept|decline|cancel|complete` — управление
  жизненным циклом обмена.
