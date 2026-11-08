# Платформа собеседований

Менеджер ведёт студента от учёбы до оффера. По карточке видно, в какую компанию человек идёт, чем закончилось собеседование и какой долг ещё не закрыт. Если после выхода на собеседования долго нет движения, студент попадает в «Грустят» и ждёт обратной связи или нового слота.

Студент входит своей учёткой и смотрит свои собеседования. Администратор смотрит всех.

Вход локальный. Демо-учётки: `admin` / `demo-admin`, `manager` / `demo-manager`, `student` / `demo-student`.

Портал на Django, DRF, Celery, PostgreSQL с pgvector, Redis и React. Один `docker-compose.yml`.

## Запуск

```bash
cp .env.example .env.local
docker compose --env-file .env.local up --build
```

Сайт: http://localhost:82. API напрямую: http://localhost:8001. Документация API: http://localhost:82/api/docs/.

Учебные записи:

```bash
docker compose --env-file .env.local exec web python manage.py seed_demo_data
```

Остальные команды: `make help`.

## Чем отличается от рабочей версии

Рабочая система ходила во внешний вход и хранила боевые карточки. Здесь этого нет.

- Вход локальный: администратор, менеджер и студент. Отдельного сервера входа нет.
- В карточке студента нет паролей внешних площадок, сессии бота и внешнего RAG.
- Нет выгрузки собеседований в таблицу и колонки статуса бота в долгах.
- Один `docker-compose.yml`. Отдельного стенда и боевого деплоя нет.
- S3, Deepgram и Яндекс Диск в `.env.example` — пустые заглушки. Без них списки и вход работают.

## Тесты

Виртуальное окружение: `python3 -m venv .venv && source .venv/bin/activate && poetry install`, либо `make install`.

`make test` — pytest на SQLite. `make coverage` — HTML в `htmlcov/index.html`. `make test-frontend` — Vitest.

Что именно покрыто: `docs/product/coverage.md`.

## Документация

Требования и сценарии: `docs/product/`. Контракт API: `docs/api/openapi.yaml`. У каждого Django-приложения свой `README.md`.

Лицензия: MIT, текст в `LICENSE`.
