# directions

Справочник направлений подготовки и аналитика собеседований по направлениям. UI — React SPA; бэкенд — REST API.

## Назначение

- CRUD направлений (создание — админ).
- Метрики: интервью, тех. интервью, уникальные кандидаты, конверсия screening → tech, предстоящие, последняя дата.
- Наблюдения и инсайты (`/api/observations/directions/`).
- Кэш аналитики в Redis.

## Структура

```
directions/
├── models.py
├── analytics_views.py     # compute_direction_metrics, observations
├── serializers.py
├── api/
│   ├── urls.py
│   └── views.py           # DirectionViewSet, analytics, observations
└── api_urls.py
```

## Модели

**Direction:** `name` (CharField). Ссылаются: `interviews`, `interns`, `offers`, `debts`.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/directions/` | Менеджер/Админ | Список (`q`) |
| GET | `/api/directions/{id}/` | То же | Детали |
| POST | `/api/directions/` | Админ | Создание |
| GET | `/api/analytics/directions/` | Менеджер/Админ | Метрики |
| GET | `/api/observations/directions/` | Менеджер/Админ | Наблюдения |

## Доступ

- `IsManagerOrAdmin` / `IsReadOnlyHROutstaff`; создание — `IsAdminRole`.

## Зависимости

- `interviews` — агрегации
- `core.decorators` — кэш аналитики

## Тесты

- `tests/test_directions/test_analytics.py` — метрики и observations
- `tests/test_directions/test_api_views.py` — ViewSet, create, фильтры, права

Запуск: `pytest tests/test_directions/ -v`
