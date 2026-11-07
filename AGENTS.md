# AGENTS.md

## Профиль репозитория

| Поле | Значение |
|---|---|
| Тип | `web-api` |
| HTTP API | да, контракт: `docs/api/openapi.yaml` |
| UI prototype | React SPA; brownfield-прототип фиксируется в `docs/product/prototype/` |
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
Видимые изменения UI синхронизировать с требованиями, тест-кейсами и реестром экранов.

## Требования и тестирование

- Требования: `docs/product/requirements.md`.
- Продуктовые сценарии: `docs/product/test-cases.md`.
- Реестр UI: `docs/product/screens-index.md`.
- Нормативы тестирования: `docs/testing/requirements.md`.
- API-контракт: `docs/api/openapi.yaml`.

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

Перед изменением API обновлять OpenAPI в том же изменении. Новый или изменённый функциональный
сценарий должен иметь тест-кейс и, где возможно, автотест. Не перемещать runtime-каталоги
`staticfiles/`, `media/`, `private_uploads/`, `logs/`, `credentials/` без копии.
