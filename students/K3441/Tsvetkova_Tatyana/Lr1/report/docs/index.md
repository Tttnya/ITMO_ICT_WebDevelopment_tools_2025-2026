# Bookcrossing API

**Отчёты по лабораторным работам** курса «Web-Программирование» (весенний семестр).

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

!!! success "ЛР3 — Docker, источники данных, очередь (100%)"
    * FastAPI-приложение, PostgreSQL и парсер упакованы в Docker (`docker-compose.yml`, 5 сервисов)
    * Отдельный контейнер-сервис парсера, вызываемый по HTTP из основного API (`/parsing/sync`)
    * Парсинг через очередь задач: Celery + Redis, эндпоинты `/parsing/async` и `/parsing/async/{task_id}`
    * Общая логика парсинга переиспользуется HTTP-сервисом и Celery-воркером без дублирования кода

## Навигация по отчёту

### ЛР1 — Bookcrossing API

* [Обзор проекта](report/overview.md) — структура папок и назначение файлов
* [Модель данных](report/models.md) — все таблицы, связи, ассоциативная сущность
* [Подключение к БД](report/connection.md) — engine, session, `.env`
* [Миграции](report/migrations.md) — Alembic autogenerate
* [Авторизация и JWT](report/auth.md) — регистрация, логин, ручной guard
* [API-эндпоинты](report/endpoints.md) — все 34 эндпоинта
* [Запуск](report/run.md) — как поднять проект локально

### ЛР2 — Потоки, процессы, асинхронность

* [Обзор](lab2/overview.md) — структура и задания
* [Задача 1](lab2/task1.md) — сумма чисел: threading vs multiprocessing vs async
* [Задача 2](lab2/task2.md) — параллельный парсинг веб-страниц с сохранением в БД
* [Запуск](lab2/run.md)

### ЛР3 — Docker, источники данных, очередь

* [Обзор](lab3/overview.md) — архитектура, 5 контейнеров, общая логика парсинга
* [Подзадача 1](lab3/task1.md) — Dockerfile, docker-compose.yml, отдельный сервис-парсер
* [Подзадача 2](lab3/task2.md) — синхронный вызов парсера по HTTP
* [Подзадача 3](lab3/task3.md) — асинхронный вызов через очередь Celery + Redis
* [Запуск](lab3/run.md)

### Практики

[1.1](practices/pr1.md), [1.2](practices/pr2.md), [1.3](practices/pr3.md)
