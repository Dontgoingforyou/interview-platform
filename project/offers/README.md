# offers

Управление офферами студентов: CRUD, группировка по месяцам, фильтры, импорт Excel/CSV (Celery), аналитика. UI — React SPA; бэкенд — REST API.

## Назначение

- Список с фильтрами и action `month-groups` для ленивой подгрузки по месяцам.
- CRUD; менеджер видит офферы своих студентов.
- Импорт через `POST /api/offers/import/`.
- Аналитика: `GET /api/analytics/offers/` (кэш Redis).

## Структура

```
offers/
├── models.py
├── services.py              # OfferImportService
├── import_excel_config.py   # маппинг колонок импорта
├── serializers.py
├── drf_list_query.py
├── analytics_views.py
├── offer_analytics_drf.py
├── api/
│   ├── urls.py
│   ├── views.py             # OfferViewSet
│   └── import_views.py
└── api_urls.py
```

## Модели

**Offer:** `intern` (FK), `direction` (FK), `company`, `amount`, `month`, `year`, `created_at`, `updated_at`. Ordering по year, month.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/offers/` | Менеджер/Админ | Список (фильтры: `q`, `intern_id`, `direction_id`, `year`, `month`) |
| GET | `/api/offers/month-groups/` | То же | Группы год/месяц с счётчиками |
| POST | `/api/offers/` | Админ | Создание |
| GET/PATCH/PUT/DELETE | `/api/offers/{id}/` | Чтение — менеджер; запись/удаление — админ | CRUD |
| POST | `/api/offers/import/` | Админ | Импорт (Celery) |
| GET | `/api/analytics/offers/` | Менеджер/Админ | Аналитика |

## Доступ

- `IsManagerOrAdmin` / `IsReadOnlyHROutstaff` по действиям ViewSet; запись и удаление — `IsAdminRole`.
- Менеджер ограничен студентами по `manager_email`.

## Импорт

Форматы: `.csv`, `.xlsx`. Маппинг — `import_excel_config.py`, сервис `OfferImportService`. Celery.

## Зависимости

- `core`, `interns`, `directions`
- Redis — кэш аналитики

## Тесты

- `tests/test_offers/test_models.py` — модель Offer
- `tests/test_offers/test_api_views.py` — REST API, month-groups, импорт
- `tests/test_offers/test_analytics.py` — аналитика
- `tests/test_offers/test_serializers.py` — сериализаторы
- `tests/test_offers/test_services.py` — импорт

Запуск: `pytest tests/test_offers/ -v`
