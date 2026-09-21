# Запуск проекта

## 1. Клонировать репозиторий

```bash
git clone https://github.com/<username>/<repo>.git
cd <repo>
```

## 2. Виртуальное окружение

```bash
python -m venv .venv
source .venv/bin/activate            # macOS / Linux
# .venv\Scripts\activate             # Windows

pip install -r requirements.txt
```

## 3. `.env`

Создать в корне проекта файл `.env` (шаблон):

```env
DB_ADMIN=postgresql://postgres:123@localhost/bookcrossing_db
JWT_SECRET=your-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

Создать саму базу в PostgreSQL (один раз):

```bash
createdb -U postgres bookcrossing_db
```

## 4. Миграции

```bash
alembic upgrade head
```

## 5. Запуск сервера

```bash
uvicorn app.main:app --reload
```

* API: <http://127.0.0.1:8000/>
* Swagger UI: <http://127.0.0.1:8000/docs>
* ReDoc: <http://127.0.0.1:8000/redoc>

## Файл `requirements.txt`

```
fastapi[all]>=0.110.0
sqlmodel>=0.0.16
psycopg2-binary>=2.9.9
alembic>=1.13.1
python-dotenv>=1.0.1
PyJWT>=2.8.0
bcrypt>=4.1.2
uvicorn[standard]>=0.29.0
```
