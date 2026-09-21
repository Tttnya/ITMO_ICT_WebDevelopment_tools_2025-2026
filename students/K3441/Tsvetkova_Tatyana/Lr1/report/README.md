# Отчёт по ЛР1 — Bookcrossing API

**Автор:** Цветкова Татьяна Александровна, группа K3441.

Отчёт в формате Markdown + MkDocs Material, как требует методичка курса.

## Локальный просмотр

Из папки `Lr1/report/`:

```bash
python -m venv .venv
source .venv/bin/activate            # macOS/Linux
# .venv\Scripts\activate             # Windows
pip install mkdocs mkdocs-material

mkdocs serve
# → http://127.0.0.1:8000
```

## Публикация на GitHub Pages (опционально)

Из папки `report/`:

```bash
mkdocs gh-deploy --force
```

MkDocs соберёт сайт, запушит его в ветку `gh-pages` этого форка. GitHub
опубликует его по адресу:

```
https://Tttnya.github.io/ITMO_ICT_WebDevelopment_tools_2025-2026/
```

Перед этим в **Settings → Pages** репозитория выбрать
**Source: `gh-pages` branch**.

## Структура отчёта

```
report/
├── mkdocs.yml
├── README.md
├── .gitignore
└── docs/
    ├── index.md               # главная
    ├── report/
    │   ├── overview.md        # обзор проекта
    │   ├── models.md          # модели БД (полный код)
    │   ├── connection.md      # подключение к БД (полный код)
    │   ├── migrations.md      # Alembic (полный код)
    │   ├── auth.md            # регистрация, JWT, ручной guard
    │   ├── endpoints.md       # все 34 эндпоинта (полный код роутеров)
    │   └── run.md             # инструкция запуска проекта
    └── practices/
        ├── pr1.md             # практика 1.1
        ├── pr2.md             # практика 1.2
        └── pr3.md             # практика 1.3
```
