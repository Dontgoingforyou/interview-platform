# managers

Модель менеджеров: запись создаётся при локальном входе, дашборд команды, REST CRUD для админов. UI — React SPA (`/managers`).

## Назначение

- Модель `Manager`: email (PK), ФИО, username, группы, `is_active`, `hidden_at`.
- Дашборд: KPI, таблица менеджеров, наблюдения, графики (данные через DRF).
- Профиль текущего пользователя: `GET /api/users/me/`.
- Celery: удаление скрытых менеджеров старше 90 дней.

## Структура

```
managers/
├── models.py
├── serializers.py
├── analytics_views.py
├── dashboard_service.py
├── managers_analytics_drf.py
├── utils.py
├── tasks.py
├── api/
│   ├── urls.py
│   └── views.py           # ManagerViewSet, analytics
└── api_urls.py
```

## Модели

**Manager:** `email` (PK), `full_name`, `username`, `groups` (JSON), `is_active`, `hidden_at`, timestamps. Свойства: `is_admin`, `is_employment_manager`, `is_cv_manager`, `is_education_manager`. Таблица `managers`.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/analytics/managers/` | Менеджер/Админ | KPI |
| GET | `/api/analytics/managers/observations/` | То же | Наблюдения |
| GET | `/api/analytics/managers/table/` | То же | Таблица дашборда |
| GET | `/api/managers/` | Админ | Список менеджеров |
| GET/PATCH | `/api/managers/{email}/` | Админ | Детали / обновление |
| PATCH | `/api/managers/{email}/update/` | Админ | Обновление (в т.ч. is_active) |
| GET | `/api/managers/for-filters/` | Менеджер/Админ | Список для фильтров |
| GET | `/api/users/me/` | Авторизованный | Текущий пользователь |

Скрытие менеджера: `POST /api/employees/set-manager-active/`.

## Доступ

- DRF: `IsManagerOrAdmin` для аналитики; `IsAdminRole` — CRUD менеджеров.
- Запись `Manager` создаётся при локальном входе в `accounts`.

## Зависимости

- `accounts` — локальный вход
- `interviews`, `directions`, `interns`
- Celery, Redis

## Тесты

- `tests/test_managers/test_models.py` — модель, свойства групп
- `tests/test_managers/test_serializers.py` — сериализаторы
- `tests/test_managers/test_utils.py` — `get_inactive_intern_ids`
- `tests/test_managers/test_api_views.py` — ViewSet, me, for-filters
- `tests/test_managers/test_analytics.py` — аналитика и table DRF
- `tests/test_managers/test_tasks.py` — `delete_stale_hidden_managers`

Запуск: `pytest tests/test_managers/ -v`
