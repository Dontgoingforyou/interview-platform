# Доступ к vector_search

Поиск, похожие сущности и статистика требуют локальную сессию.

Администратор видит все записи. Менеджер — только те, где `metadata.manager_email` совпадает с почтой из сессии. Чужой `manager_email` в запросе даёт 403.

Эндпоинты: `POST /api/vector/search/`, `POST /api/vector/similar/`, `GET /api/vector/stats/`.

Запрос пишется в `SearchLog`: фильтры и число результатов. Email в лог не попадает.
