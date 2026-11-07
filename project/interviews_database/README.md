# interviews_database

Реестр собеседований с записью созвона или видео: непустой `link`, `video_link` или активная загрузка (`upload_task_id`). Только просмотр через REST API; HTML-шаблоны и `views.py` удалены. UI — React SPA.

## Назначение

- Единый список из `interviews.Interview` по условию наличия медиа-ссылки или `upload_task_id`.
- Фильтры: менеджер, направление, компания, тип собеседования, статус транскрипции, текстовый поиск, сортировка.
- Все менеджеры видят все записи реестра (без фильтра по своему email); доступ по роли `IsManagerOrAdmin`.
- Общий queryset: `interviews.interview_list.build_interviews_database_api_queryset`.

## Структура

```
interviews_database/
├── api/
│   ├── urls.py
│   └── views.py           # InterviewsDatabaseListAPIView
├── api_urls.py
└── apps.py
```

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/interviews-database/` | `IsManagerOrAdmin` | Список (`ListPagination`, page_size по умолчанию 20) |

Параметры: `q`, `company`, `interview_type`, `manager`, `direction` / `direction_id`, `transcription`, `order_by`, `order_dir`, `page`, `page_size`.

## Доступ

- DRF: `IsManagerOrAdmin`, локальная сессия.
- HR и outstaff: чтение в рамках разрешённых разделов (см. `core.constants`).

## Зависимости

- `interviews` — модель Interview, сборка queryset
- `companies` — фильтр по компании
- `core.pagination` — ListPagination

## Тесты

- `tests/test_interviews_database/test_api.py` — REST `/api/interviews-database/`

Запуск: `pytest tests/test_interviews_database/ -v`
