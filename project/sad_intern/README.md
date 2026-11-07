# sad_intern

Студенты, долго ожидающие собеседований или обратной связи («грустящие»). Группировка по направлениям, статусы записи, синхронизация с `Intern.real_interview_date` по сигналу. UI — React SPA; бэкенд — REST API.

## Назначение

- Плоский список, группировка по направлениям (`grouped`), блок «вышли на проект» (`on-project`).
- CRUD, аналитика (`/api/analytics/sad-intern/`), импорт из Excel/CSV (Celery).
- Автосоздание/обновление по `Intern.post_save` при условиях из `core.constants` (`SAD_INTERN_ELIGIBLE_MIN_REAL_INTERVIEW_DATE`, менеджер, дата).
- Статус `on_project` — вручную (API/импорт), не через Offer/Debt.

## Структура

```
sad_intern/
├── models.py
├── managers.py              # SadInternManager, SadInternQuerySet
├── services.py              # SadInternImportService
├── import_excel_config.py   # маппинг колонок импорта
├── serializers.py
├── drf_list_query.py
├── analytics_views.py
├── sad_intern_analytics_drf.py
├── signals.py
├── api/
│   ├── urls.py
│   ├── views.py             # SadInternViewSet
│   └── import_views.py
└── api_urls.py
```

## Модели

**SadIntern:** `intern` (FK), `date_added`, `waiting_since`, `days_waiting`, `telegram_username`, `manager_email`, `status`, `note`. ExternalReferencesMixin. QuerySet: `for_main_waiting_list()`, фильтрация оффер/ушёл через `Intern.manual_status`.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/sad-interns/` | Менеджер/Админ/HR/outstaff (read-only) | Плоский список (`exclude_on_project=false` — расширенный) |
| GET | `/api/sad-interns/grouped/` | То же | Группы по направлениям |
| GET | `/api/sad-interns/on-project/` | То же | Вышли на проект |
| POST | `/api/sad-interns/` | Менеджер/Админ (запись) | Создание |
| GET/PATCH/PUT | `/api/sad-interns/{id}/` | Чтение — менеджер; запись — по роли | Детали / обновление |
| DELETE | `/api/sad-interns/{id}/` | Админ | Удаление |
| GET | `/api/analytics/sad-intern/` | Менеджер/Админ | Метрики |
| POST | `/api/sad-interns/import/` | Админ | Импорт (Celery) |

## Доступ

- `IsManagerOrAdmin` + `IsReadOnlyHROutstaff` для чтения и записи менеджером; `IsAdminRole` — destroy и импорт.
- Менеджер видит записи в рамках `sad_intern_role_scoped_qs`.

## Импорт

Форматы: `.csv`, `.xlsx`. Маппинг — `import_excel_config.py`, логика — `SadInternImportService`. Celery, статус через `/import/status/<task_id>/`.

## Зависимости

- `core`, `interns`, `managers`, `directions`
- Celery, Redis

## Тесты

- `tests/test_sad_intern/test_models.py` — модель, QuerySet
- `tests/test_sad_intern/test_api_views.py` — ViewSet, grouped, on-project
- `tests/test_sad_intern/test_analytics_views.py` — аналитика
- `tests/test_sad_intern/test_serializers.py` — сериализаторы
- `tests/test_sad_intern/test_services.py` — импорт
- `tests/test_sad_intern/test_signals.py` — синхронизация с Intern
- `tests/test_sad_intern/test_utils.py` — утилиты

Запуск: `pytest tests/test_sad_intern/ -v`
