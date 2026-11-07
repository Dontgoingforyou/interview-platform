# interns

Управление студентами: CRUD, фильтрация, поиск, импорт из Excel/CSV. Интерфейс — React SPA; бэкенд — только REST API под `/api/`. Связь с `directions.Direction`, назначение менеджера по email.

## Назначение

- Список студентов с поиском (ФИО, email, группа, HR), фильтрами (менеджер, направление, статус), сортировкой. Менеджер видит только своих по `manager_email`; админ, HR и outstaff — всех (HR/outstaff — только чтение).
- Создание и обновление студентов через API; удаление — только админ. Синхронизация с SadIntern при изменении `real_interview_date`.
- Импорт студентов и отдельный импорт дат реальных собеседований (Celery, только админ).
- Action `manual-status` — смена `manual_status`.

## Структура

```
interns/
├── models.py              # Intern
├── api/
│   ├── urls.py
│   ├── views.py           # InternViewSet
│   └── import_views.py    # InternImportAPIView, InternImportDatesAPIView
├── api_urls.py
├── services.py            # InternImportService, InternSyncImportService, RealInterviewDateImportService
├── utils.py
├── validators.py
├── list_filters.py
├── serializers.py
├── pagination.py
└── apps.py
```

## Модели

**Intern:** `manager_email`, `full_name`, `email`, `corporate_email` (почта входа на портал), `telegram_username`, `direction` (FK), `city`, `cv`, даты приёма/рождения, HR-поля, `group`, `type_of_training`, `legend`, отзывы, `real_interview_date`, `manual_status`, `inactive_since`. Свойства: `status`, `status_display`. Таблица `interns`.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/interns/` | Менеджер/Админ/HR/outstaff (read-only) | Список (фильтры: `q`, `status`, `manager`, `direction_id`, `group`, сортировка) |
| POST | `/api/interns/` | Админ или роль записи интервью | Создание (`manager_email` из сессии для не-админа) |
| GET | `/api/interns/{id}/` | То же | Детали |
| PUT/PATCH | `/api/interns/{id}/` | Админ | Обновление |
| DELETE | `/api/interns/{id}/` | Админ | Удаление |
| PATCH | `/api/interns/{id}/manual-status/` | Менеджер (свои) / Админ | Смена `manual_status` |
| POST | `/api/interns/import/` | Админ | Импорт студентов (Celery), только новые записи |
| POST | `/api/interns/import-sync/` | Админ | Синхронизация из файла (merge-only: дополняет пустые поля) |
| POST | `/api/interns/import-dates/` | Админ | Импорт дат реальных собеседований |

## Доступ

- DRF: `IsManagerOrAdmin` + `IsReadOnlyHROutstaff` для чтения; `IsAdminRole` — update/destroy; `IsInterviewWriteRole` — create.
- HR и outstaff: просмотр и фильтрация без записи (см. `accounts.permissions`, `core.constants`).

## Импорт

Форматы: `.csv`, `.xlsx`, `.xls`. Три эндпоинта: полный импорт (только новые), синхронизация (merge-only) и импорт дат. Celery, регистрация владельца задачи через `core.import_tasks`. Статус: `/import/status/<task_id>/`.

Колонки полного импорта/синхронизации — см. `INTERN_IMPORT_COLUMN_MAPPING` в `core/constants.py` (ФИО, Направление, Город, CV, CV (ау) и др.).

CLI (локальная проверка): `python manage.py sync_interns_from_file --file <path> [--dry-run]`.

## Зависимости

- `core` — импорт, фильтры, валидаторы, константы статусов
- `directions`, `managers`, `sad_intern`
- Celery, Redis

## Тесты

- `tests/test_interns/test_models.py` — Intern, статусы
- `tests/test_interns/test_api_views.py` — REST API, manual-status, импорт
- `tests/test_interns/test_services.py` — сервисы импорта
- `tests/test_interns/test_validators.py` — валидаторы даты рождения, Telegram
- `tests/test_interns/test_utils.py` — утилиты

Запуск: `pytest tests/test_interns/ -v`
