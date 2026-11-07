# companies

Справочник компаний для собеседований: CRUD, статистика, объединение дублей. UI — React SPA; бэкенд — REST API.

## Назначение

- Список с поиском и фильтром `is_bigtech`.
- Редактирование, удаление (запрет при связанных собеседованиях).
- Объединение дублей: перенос собеседований, слияние `aliases`.
- Статистика для шапки списка.

## Структура

```
companies/
├── models.py
├── services.py            # MergeCompaniesService, stats
├── serializers.py
├── api/
│   ├── urls.py
│   ├── views.py           # CompanyViewSet, stats, merge
│   └── permissions.py     # IsCompanyEditor
└── api_urls.py
```

## Модели

**Company:** `name`, `is_bigtech`, `aliases` (текст, по строке). Метод `get_aliases_list()`. Используется в `interviews.Interview` и импорте (`get_or_create_company`).

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/companies/` | `IsManagerOrAdmin` | Список (`q`, `is_bigtech`) |
| GET | `/api/companies/{id}/` | То же | Детали |
| POST/PATCH/PUT/DELETE | `/api/companies/...` | `IsCompanyEditor` (админ) | CRUD |
| GET | `/api/companies/stats/` | Менеджер/Админ | Сводные числа |
| POST | `/api/companies/merge/` | Админ | Объединение дублей |

## Доступ

- Чтение: `IsManagerOrAdmin`.
- Запись и merge: `IsCompanyEditor` (администратор).

## Зависимости

- `interviews` — FK Company, импорт по aliases
- `core.logging_mixins`

## Тесты

- `tests/test_companies/test_api_views.py` — REST API (list, CRUD, stats, merge, права)

Запуск: `pytest tests/test_companies/ -v`
