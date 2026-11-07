# core

Ядро платформы: настройки Django, корневой URLconf, React SPA, базовые сервисы импорта, миксины доступа и логирования, middleware, утилиты, Celery.

## Назначение

- Маршрутизация: React SPA (`ReactSPAView`) и REST под `/api/`. `GET /accounts/login/` перенаправляет на `/login`.
- Миксины доступа и логирования для DRF и оставшегося server-side кода (`mixins`, `logging_mixins`).
- Импорт: `BaseImportService`, Celery `async_import_from_file`, IDOR-защита статуса (`import_tasks`).
- HR/outstaff: `HROutstaffRedirectMiddleware`, `can_write` в контексте.
- Автодополнение Select2: `autocomplete.py`.
- Swagger/ReDoc под `/api/docs/` (только для авторизованных менеджеров/админов).

## Структура

```
core/
├── settings.py
├── urls.py                # API includes + ReactSPAView catch-all
├── celery.py
├── views.py               # GetInternDataView, ImportTaskStatusView, ProtectedSwagger*
├── base_services.py
├── mixins.py
├── logging_mixins.py
├── decorators.py
├── middleware.py
├── import_tasks.py
├── autocomplete.py
├── pagination.py
├── file_utils.py
├── date_utils.py
├── intern_utils.py
├── constants.py
├── validators.py
├── context_processors.py
└── management/commands/
    └── seed_demo_data.py
```

`python manage.py seed_demo_data` создаёт учебные направления, компании, студентов, собеседования, офферы, долг с платежами, «Грустят», недельный статус, транскрипцию и статью базы знаний. Повторный запуск не плодит дубли.

## URL и представления

Собственные эндпоинты core (не приложения):

| URL | View | Описание |
|-----|------|----------|
| `/api/intern-data/` | `GetInternDataView` | Данные студента для форм |
| `/import/status/<task_id>/` | `ImportTaskStatusView` | Статус Celery-импорта |
| `/api/schema/` | `ProtectedSchemaView` | OpenAPI schema, только при `DEBUG=True` |
| `/api/docs/` | `ProtectedSwaggerView` | Swagger UI, только при `DEBUG=True` |
| `/api/redoc/` | `ProtectedRedocView` | ReDoc, только при `DEBUG=True` |
| `/`, `/<path:path>` | `ReactSPAView` | React SPA (кроме `/accounts/`, `/api/`) |

Подключение API приложений — в `core/urls.py` (`path('api/', include(...))`).

## Доступ

- Миксины `ManagerRequiredMixin`, `AdminRequiredMixin`, `RoleBasedAccessMixin`, `InternPortalRequiredMixin` — для оставшегося server-side кода.
- Swagger, ReDoc и `/api/schema/` — только при `DEBUG=True`, затем менеджер или администратор. При `DEBUG=False` — 404.
- Вход — `accounts/README.md`.

## Зависимости

- Django, Celery, Redis, DRF, drf-spectacular
- Все доменные приложения подключаются через `urls.py`

## Тесты

- `tests/test_core/test_autocomplete.py` — автодополнение
- `tests/test_core/test_base_services.py` — BaseImportService
- `tests/test_core/test_celery.py` — Celery-конфигурация
- `tests/test_core/test_common_extras.py` — общие утилиты шаблонов
- `tests/test_core/test_date_utils.py` — даты
- `tests/test_core/test_decorators.py` — декораторы, кэш аналитики
- `tests/test_core/test_file_utils.py` — файлы
- `tests/test_core/test_import_tasks.py` — импорт, владелец задачи
- `tests/test_core/test_intern_utils.py` — привязка студента, транслит
- `tests/test_core/test_logging_mixins.py` — логирование CRUD
- `tests/test_core/test_middleware.py` — middleware HR/outstaff, студенты
- `tests/test_core/test_mixins.py` — миксины доступа
- `tests/test_core/test_urls.py` — корневой urlconf
- `tests/test_core/test_views.py` — GetInternData, ImportTaskStatus, Swagger

Запуск: `pytest tests/test_core/ -v`
