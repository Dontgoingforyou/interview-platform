# Стратегия тестирования

Тестирование ведётся от требований и продуктовых сценариев:

1. Unit — функции, сервисы, сериализаторы и React-компоненты.
2. Integration — Django ORM, API views, Celery и внешние адаптеры с mock.
3. Contract/API — соответствие DRF API версии `docs/api/openapi.yaml`.
4. E2E — ключевые пользовательские маршруты React через Playwright.

Backend-тесты находятся в `tests/`, frontend unit-тесты — в
`project/frontend/src/tests/`, E2E — в `project/frontend/e2e/`.
