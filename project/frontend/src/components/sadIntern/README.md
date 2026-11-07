# Компоненты раздела «Грустят» (`sad_intern`)

Модуль UI для списка ожидания студентов (маршрут `/sad-intern`).

- **`analytics/`** — сетка метрик (данные с `GET /api/analytics/sad-intern/`).
- **`filters/`** — поиск `q`, статус, направление; синхронизация с query string (`sadInternListParams`).
- **`list/`** — группа по направлению с пагинацией `page_<id|none>`, таблица блока «Вышли на проект».

Страницы: `pages/sadIntern/SadInternListPage.tsx`, `pages/sadIntern/SadInternFormPage.tsx`. API: `api/sadInternApi.ts`, хуки: `hooks/sadIntern/useSadInternListPage.ts`.
