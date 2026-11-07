# Покрытие тестами

Процентный порог для бэкенда не задан. Отчёт показывает непрогнанные строки.

## Бэкенд

`make coverage` запускает pytest с coverage. Считается каталог `project/`, без миграций, тестов, `asgi.py` и `wsgi.py`. HTML — `htmlcov/index.html`, XML — `coverage.xml`. В консоли видны пропущенные строки.

Тесты идут на SQLite. Векторные сигналы выключены переменной `DISABLE_VECTOR_SIGNALS`.

## Фронтенд

`cd project/frontend && npm run test:coverage` считает Vitest-покрытие `src/utils` и `src/constants`. Порог — 90% строк. Страницы и компоненты этим процентом не покрываются: их проверяют сценарии Playwright, `npm run test:e2e`.
