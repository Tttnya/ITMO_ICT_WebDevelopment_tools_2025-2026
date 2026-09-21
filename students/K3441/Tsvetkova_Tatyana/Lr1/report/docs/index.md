# Bookcrossing API

**Отчёт по лабораторной работе №1** курса «Web-Программирование» (весенний семестр).

**Автор:** Цветкова Татьяна Александровна

**Тема:** Разработка веб-приложения для буккроссинга.

## Стек

* Python 3.10+
* [FastAPI](https://fastapi.tiangolo.com/) — веб-фреймворк
* [SQLModel](https://sqlmodel.tiangolo.com/) поверх [SQLAlchemy](https://www.sqlalchemy.org/) — ORM
* [PostgreSQL](https://www.postgresql.org/) — СУБД
* [Alembic](https://alembic.sqlalchemy.org/) — миграции
* [PyJWT](https://pyjwt.readthedocs.io/) + [bcrypt](https://github.com/pyca/bcrypt/) — токены и хэширование
* [python-dotenv](https://github.com/theskumar/python-dotenv) — переменные окружения

## Что реализовано

!!! success "Задание на 9 баллов"
    * 6 таблиц через SQLModel
    * Связи many-to-many и one-to-many
    * Ассоциативная сущность `BookGenreLink` с дополнительным полем `relevance`
    * Полноценный CRUD для всех сущностей
    * GET-запросы возвращают вложенные объекты
    * Alembic-миграции с URL из `.env`
    * Полностью аннотированные типы
    * Разбиение кода по бизнес-областям на отдельные пакеты

!!! success "Задание на 15 баллов"
    * Регистрация и логин пользователей
    * Хэширование паролей (bcrypt)
    * Генерация JWT-токенов (PyJWT)
    * **Аутентификация по JWT реализована вручную** (без сторонних библиотек-обёрток)
    * Дополнительные эндпоинты: `/auth/me`, `/users/`, `/users/{id}`, `/auth/change-password`

## Навигация по отчёту

* [Обзор проекта](report/overview.md) — структура папок и назначение файлов
* [Модель данных](report/models.md) — все таблицы, связи, ассоциативная сущность
* [Подключение к БД](report/connection.md) — engine, session, `.env`
* [Миграции](report/migrations.md) — Alembic autogenerate
* [Авторизация и JWT](report/auth.md) — регистрация, логин, ручной guard
* [API-эндпоинты](report/endpoints.md) — все 34 эндпоинта
* [Запуск](report/run.md) — как поднять проект локально
* Практики: [1.1](practices/pr1.md), [1.2](practices/pr2.md), [1.3](practices/pr3.md)
