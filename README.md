# Платформа собеседований

Личный пет-проект: студенты, собеседования, офферы и долги. Вход локальный.

Демо-учётки: `admin` / `demo-admin`, `manager` / `demo-manager`, `student` / `demo-student`.

## Запуск

```bash
cp .env.example .env.local
docker compose --env-file .env.local up --build
```

Сайт: http://localhost:82. API напрямую: http://localhost:8001. Документация API: http://localhost:82/api/docs/.

Учебные записи, если контейнер `web` уже запущен:

```bash
docker compose --env-file .env.local exec web python manage.py seed_demo_data
```

Повторный запуск не создаёт дубли. Кроме студентов и собеседований команда кладёт офферы, долг с платежами, записи «Грустят», неделю на доске сотрудников, ссылку для базы собеседований с учебной транскрипцией и статью базы знаний. Студент `student` / `demo-student` видит свои собеседования. Остальные команды: `make help`.

## Чем отличается от рабочей версии

Рабочая система ходила во внешний вход и хранила боевые карточки. Здесь этого нет.

- Вход локальный: администратор, менеджер и студент. Отдельного сервера входа нет.
- В карточке студента нет паролей внешних площадок, сессии бота и внешнего RAG.
- Нет выгрузки собеседований в таблицу и колонки статуса бота в долгах.
- Один `docker-compose.yml`. Отдельного стенда и боевого деплоя нет.
- Векторный поиск выключен флагом `DISABLE_VECTOR=true`, пока не задан свой `OPENAI_API_KEY`. Команды `vectorize_data`, `vectorize_async` и `check_vector_sync` покрывают одни и те же типы, включая транскрипции и статьи базы знаний. Сами эмбеддинги появятся только после ключа и снятия флага: существующие строки сами не индексируются.
- S3, Deepgram и Яндекс Диск в `.env.example` — пустые заглушки. Без них списки и вход работают.

Виртуальное окружение для тестов и линтера: `python3 -m venv .venv && source .venv/bin/activate && poetry install`, либо `make install`.

## Стек

Django 5.2, DRF, Celery, PostgreSQL с pgvector, Redis, React 19, Vite. Один `docker-compose.yml` в корне.

Векторный поиск выключен, пока в `.env.local` стоит `DISABLE_VECTOR=true`. Чтобы включить, уберите флаг, задайте `OPENAI_API_KEY` и выполните `python manage.py vectorize_data --all`.

## Тесты

`make test` — pytest на SQLite. `make coverage` — HTML в `htmlcov/index.html`. `make test-frontend` — Vitest.

Что именно покрыто: `docs/product/coverage.md`.

## Документация

Требования и сценарии: `docs/product/`. Контракт API: `docs/api/openapi.yaml`. У каждого Django-приложения свой `README.md`.

Лицензия: MIT, текст в `LICENSE`.
