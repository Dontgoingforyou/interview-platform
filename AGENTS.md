# AGENTS.md

## Профиль репозитория

| Поле | Значение |
|---|---|
| Тип | `web-api` |
| HTTP API | да, схема собирается DRF и открывается на `/api/docs/` |
| UI | React SPA в `project/frontend/` |
| Запуск | один `docker-compose.yml` в корне |
| Submodule | нет |

## Роль

Личный пет-проект для учёта собеседований, студентов, сотрудников и офферов.
Вход локальный, демо-роли. Операции для агента доступны через `POST /mcp`.

## Стек и пути

- Backend: Python 3.12+, Django 5.2, DRF, Celery — `project/`.
- Frontend: React 19, TypeScript, Vite — `project/frontend/`.
- Tests: pytest — `tests/`; Vitest и Playwright — `project/frontend/src/tests/`,
  `project/frontend/e2e/`.
- Запуск: `docker-compose.yml` в корне. Отдельного стенда и продакшена нет.

Backend сохраняет плоские имена Django-модулей (`core`, `interns`, `interviews` и другие).
Корень `project/` должен присутствовать в `PYTHONPATH`; переименовывать модули без отдельной
задачи нельзя.

## Границы

Секреты, `.env` и ключи в Git не добавлять.

## Тестирование

- Backend: `pytest` в `tests/`.
- Frontend: Vitest в `project/frontend/src/tests/`, Playwright в `project/frontend/e2e/`.
- Новый или изменённый сценарий закрывать автотестом.

## Git

Основная ветка — `main`. Сообщение коммита: `<тип>(<область>): <описание на русском>`.
Типы: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `perf`.

## Команды

```bash
poetry install
poetry run pytest
poetry run flake8 project tests
poetry run mypy project/

cd project/frontend
npm ci
npm run test
npm run build

docker compose --env-file .env.local up --build
```

## Для агента

Схема API собирается из кода DRF. Новый или изменённый сценарий закрывать автотестом.
Не перемещать runtime-каталоги
`staticfiles/`, `media/`, `private_uploads/`, `logs/`, `credentials/` без копии.
