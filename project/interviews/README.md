# interviews

Управление собеседованиями студентов: REST API для React SPA, импорт из Excel/CSV (Celery), аналитика, транскрипции. Связи с `directions.Direction` и `companies.Company`.

## Назначение

- Список собеседований с поиском, фильтрами (менеджер, направление, компания, формат, дата), сортировкой, пагинацией (фронтенд `/interviews`).
- CRUD через API: менеджеры с правом записи создают/редактируют свои записи; удаление — админ. Импорт через Celery (`InterviewImportService`).
- REST API: список, детали, CRUD, транскрипция, аналитика.

## Структура

```
interviews/
├── models.py              # Interview
├── services.py            # InterviewImportService
├── utils.py
├── serializers.py
├── analytics_views.py     # compute_interview_analytics (для DRF)
├── interview_list.py      # queryset списка и БД собеседований
├── api/
│   ├── views.py           # InterviewViewSet
│   ├── urls.py
│   ├── import_views.py
│   ├── interview_analytics.py
│   └── config_views.py    # deepgram-balance
└── api_urls.py            # include в core/urls.py → /api/
```

## Модели

**Interview:** `intern` (FK), `direction`, `company`, `manager_email`, `interview_type`, `interview_format`, `date`, `time`, `link`, `vacancy_link`, `interview_link`, `video_link`, `upload_task_id`, `hr_name`, `hr_contacts`, `created_at`, `updated_at`.

## URL и представления

Интерфейс — React SPA (`/interviews`, `/interviews/new/`, …). Бэкенд — префикс `/api/` (см. `interviews/api/urls.py`).

### REST API

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/interviews/` | Менеджер/HR/outstaff/Админ | Список с фильтрами |
| POST | `/api/interviews/` | Запись (менеджер/админ) | Создать |
| GET | `/api/interviews/{id}/` | Менеджер/HR/outstaff/Админ | Детали |
| PATCH | `/api/interviews/{id}/` | Админ | Обновить |
| DELETE | `/api/interviews/{id}/` | Админ | Удалить |
| POST | `/api/interviews/{id}/transcribe/` | Админ | Запуск транскрипции |
| GET | `/api/interviews/{id}/transcription-status/` | Менеджер/Админ | Статус транскрипции |
| GET | `/api/interviews/{id}/transcription-text/` | Менеджер/Админ | Текст транскрипции |
| GET | `/api/analytics/interviews/` | Менеджер/Админ | Аналитика |
| GET | `/api/analytics/interviews/type-breakdown/` | Менеджер/Админ | Разбивка по типам |
| POST | `/api/interviews/import/` | Админ | Импорт файла (Celery) |
| GET | `/api/import/status/{task_id}/` | Владелец задачи | Статус импорта |
| GET | `/api/transcriptions/deepgram-balance/` | Админ | Баланс Deepgram |

Статус импорта (общий): `GET /import/status/<task_id>/` в `core.urls`.

## Доступ

- API: ViewSet + `interview_list.py` (фильтры/сортировка). Админ — полный доступ; менеджер — только свои по `manager_email`.
- API: `IsManagerOrAdmin` (GET), `IsAdminRole` (create/update/delete).

## Импорт

Форматы: `.csv`, `.xlsx`. Асинхронно через Celery. Маппинг — `INTERVIEW_COLUMN_MAPPING` в `core.constants`, логика в `InterviewImportService`. Статус: `/api/import/status/<task_id>/` или `/import/status/<task_id>/`.

## Зависимости

- `core` — import_tasks, constants, pagination
- `interns`, `directions`, `companies`, `managers`, `transcriptions`
- Celery, Redis

## Тесты

- `tests/test_interviews/test_models.py` — модели
- `tests/test_interviews/test_services.py` — импорт
- `tests/test_interviews/test_utils.py`, `test_serializers.py`, `test_analytics.py`
- `tests/test_interviews/test_api_views.py` — REST API, транскрипция

Запуск: `pytest tests/test_interviews/ -v`
