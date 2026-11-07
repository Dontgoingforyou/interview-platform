# developers

Сводный список специалистов (студентов) с собеседованиями или офферами: статистика, аналитика, экспорт Excel. UI — React SPA; бэкенд — REST API.

## Назначение

- Пагинированный список с фильтрами (`q`, направление), сортировкой.
- Аналитика: активность за 15 дней, средний оффер, топ направлений (кэш Redis).
- Экспорт таблицы, метрик и графика в Excel.

## Структура

```
developers/
├── analytics_views.py     # get_developers_stats, analytics
├── services.py            # DeveloperExportService
├── serializers.py
├── api/
│   ├── urls.py
│   ├── views.py           # stats, analytics
│   └── export_views.py
└── api_urls.py
```

## Модели

Собственных моделей нет; агрегации по `interns`, `interviews`, `offers`, `directions`.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/developers/` | Менеджер/Админ | Список специалистов |
| GET | `/api/analytics/developers/` | То же | JSON аналитики |
| GET | `/api/developers/export/table/` | То же | Excel таблицы |
| GET | `/api/developers/export/metrics/` | То же | Excel метрик |
| GET | `/api/developers/export/chart/` | То же | Excel графика |

## Доступ

- `IsManagerOrAdmin` + `IsReadOnlyHROutstaff` для чтения и экспорта.

## Зависимости

- `interns`, `interviews`, `offers`, `directions`
- Redis — кэш `developer_analytics_api`

## Тесты

- `tests/test_developers/test_api_views.py` — список, аналитика, экспорт
- `tests/test_developers/test_services.py` — Excel-экспорт
- `tests/test_developers/test_analytics.py` — расчёт метрик

Запуск: `pytest tests/test_developers/ -v`
