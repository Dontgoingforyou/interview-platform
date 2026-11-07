# Платформа собеседований

Личный пет-проект: студенты, собеседования, офферы и долги. Вход локальный.

Демо-учётки: `admin` / `demo-admin`, `manager` / `demo-manager`, `student` / `demo-student`.

## Запуск

```bash
cp .env.example .env.local
docker compose --env-file .env.local up --build
```

Сайт: http://localhost:82. API напрямую: http://localhost:8001. Документация API: http://localhost:82/api/docs/.

Демо-данные: `make mock`. Остальные команды: `make help`.

Виртуальное окружение для тестов и линтера: `python3 -m venv .venv && source .venv/bin/activate && poetry install`, либо `make install`.

## Стек

Django 5.2, DRF, Celery, PostgreSQL с pgvector, Redis, React 19, Vite. Один `docker-compose.yml` в корне.

Векторный поиск выключен, пока в `.env.local` стоит `DISABLE_VECTOR=true`. Чтобы включить, уберите флаг и задайте `OPENAI_API_KEY`.

## Тесты

`make test` — pytest на SQLite. `make coverage` — тот же прогон с отчётом, HTML в `htmlcov/index.html`. Порог для бэкенда не задан.

`make test-frontend` — Vitest. Покрытие `src/utils` и `src/constants`, порог 90% строк: `cd project/frontend && npm run test:coverage`.

Как устроены отчёты: `docs/product/coverage.md`.

## Документация

Требования и сценарии: `docs/product/`. Контракт API: `docs/api/openapi.yaml`. У каждого Django-приложения свой `README.md`.

Лицензия: MIT, текст в `LICENSE`.
