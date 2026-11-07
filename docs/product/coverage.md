# Покрытие тестами

`make test` гоняет pytest на SQLite. `make coverage` пишет HTML в `htmlcov/index.html`. Миграции в отчёт не входят, порог для бэкенда не задан.

Бэкенд закрыт примерно на 90% строк (3064 теста). Тоньше всего команды `vectorize_data` и `sync_interns_from_file`.

Vitest считает `src/utils` и `src/constants`, порог 90% строк: `cd project/frontend && npm run test:coverage`. Страницы в этот процент не входят. Playwright — два смока, `npm run test:e2e`: вход открывает собеседования, раздел сотрудников показывает заголовок.

Сценарии продукта: `docs/product/test-cases.md`.
