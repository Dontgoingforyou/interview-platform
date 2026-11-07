# debts

Учёт долгов студентов: суммы, история платежей по месяцам, импорт, аналитика, представление «по месяцам». UI — React SPA; бэкенд — REST API.

## Назначение

- CRUD долгов, action `add-payment`, список `by-month`.
- Импорт долгов и платежей (Celery).
- Аналитика: `GET /api/analytics/debts/`.

## Структура

```
debts/
├── models.py              # Debt, PaymentHistory
├── services.py            # DebtImportService
├── import_excel_config.py
├── analytics_views.py
├── debt_analytics_drf.py
├── drf_list_query.py
├── drf_by_month.py
├── serializers.py
├── utils.py
├── api/
│   ├── urls.py
│   ├── views.py           # DebtViewSet
│   └── import_views.py
└── api_urls.py
```

## Модели

**Debt:** `intern`, `direction` (nullable), статусы, контакты, `total_amount`, `paid_amount`, `balance`, `act_date`. **PaymentHistory:** `debt`, `month`, `year`, `amount` — unique `(debt, month, year)`.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/debts/` | Менеджер/Админ | Список |
| GET | `/api/debts/by-month/` | То же | Группировка по месяцам |
| POST | `/api/debts/` | Админ | Создание |
| GET/PATCH | `/api/debts/{id}/` | Чтение — менеджер; запись — админ | Детали / обновление |
| POST | `/api/debts/{id}/add-payment/` | Админ | Платёж за месяц |
| DELETE | `/api/debts/{id}/` | Админ | Удаление |
| POST | `/api/debts/import/` | Админ | Импорт |
| GET | `/api/analytics/debts/` | Менеджер/Админ | Аналитика |

## Доступ

- `IsManagerOrAdmin` + `IsReadOnlyHROutstaff`; запись и импорт — `IsAdminRole`.

## Импорт

Форматы: `.csv`, `.xlsx`. `DebtImportService`, Celery.

## Зависимости

- `core`, `interns`, `directions`
- Redis — кэш аналитики

## Тесты

- `tests/test_debts/test_models.py` — Debt, PaymentHistory
- `tests/test_debts/test_api_views.py` — ViewSet, by-month, add-payment
- `tests/test_debts/test_services.py` — импорт
- `tests/test_debts/test_analytics.py` — аналитика
- `tests/test_debts/test_serializers.py` — сериализаторы
- `tests/test_debts/test_utils.py` — утилиты

Запуск: `pytest tests/test_debts/ -v`
