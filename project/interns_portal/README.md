# interns_portal

Портал студента (React SPA, маршрут `/interns-portal/`): список своих собеседований и асинхронная загрузка записи видео в S3 (FirstVDS). Бэкенд — только REST API; HTML-`views.py` удалён.

## Назначение

- Список собеседований студента (пагинация 20), без типов «Тестовое задание» и «Анкета с большим кол-вом технички».
- Привязка `Intern` при входе: почта входа, ФИО (транслит и эвристики в `core.intern_utils`).
- Загрузка видео (multipart) → Celery → `Interview.video_link`; статус задачи по `upload_task_id` с защитой от гонок (`select_for_update`, sentinel `__uploading__`).
- После входа студент с группой `students` перенаправляется на `/interns-portal/`.

## Структура

```
interns_portal/
├── api/
│   ├── urls.py
│   ├── views.py           # список, upload, статус задачи
│   └── serializers.py
├── api_urls.py
├── services.py            # get_intern_for_portal_user
├── constants.py           # форматы видео, скрытые типы собеседований
├── upload_logging.py      # [PORTAL_UPLOAD] фазы логов
├── yandex_upload.py       # build_video_object_filename
├── tasks.py               # upload_video_to_s3
└── apps.py
```

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/interns-portal/interviews/` | `IsInternPortalStudent` | Пагинированный список собеседований |
| POST | `/api/interns-portal/interviews/<id>/upload/` | То же | multipart `video`, ответ `{ task_id }` |
| GET | `/api/interns-portal/upload-tasks/<task_id>/` | То же | Статус Celery, если задача принадлежит студенту |

## Доступ

- `IsInternPortalStudent` (`accounts.permissions`) — только «чистый» студент (группа `students`, без админа и менеджерских групп).
- Аутентификация: сессия локального входа.

## Загрузка видео

- Лимит 10 ГБ; форматы из `constants.py` (`.mp4`, `.mov`, …).
- Временный файл → `PRIVATE_UPLOAD_ROOT/intern_uploads/` → Celery → S3 (`interview-videos`, плоский ключ `{имя файла}` в корне бакета) → стабильный URL в `Interview.video_link`; просмотр — presigned при отдаче API.
- **Docker:** каталог `./private_uploads` должен быть смонтирован в контейнеры `web` и `celery_worker` (общий volume), иначе worker не увидит файл после POST.
- На хосте при деплое: `mkdir -p private_uploads/intern_uploads` (каталог в `.gitignore`).
- Gunicorn: `--timeout 7200` (согласовано с nginx для больших POST).
- Параллельные загрузки — sentinel `__uploading__` + очередь Celery.

### Поведение при ошибке Celery

При неудаче задачи (`MaxRetriesExceededError` или жёсткий kill) `upload_task_id` остаётся в БД — это намеренно: статусный эндпоинт увидит состояние `FAILURE` по `task_id`, сбросит слот (`upload_task_id = None`) и вернёт ошибку студенту. После следующего рефетча списка студент увидит кнопку «Загрузить» снова.

Поэтому задача **не имеет** `soft_time_limit` / `time_limit` в декораторе — они несовместимы с `--pool=threads` (используется в production): `soft_time_limit` игнорируется, а `time_limit` убивает весь процесс воркера целиком, не давая запустить cleanup.

Очистка зависшего `upload_task_id` вручную (если студент завис без доступа к порталу):

```sql
UPDATE interviews SET upload_task_id = NULL
WHERE upload_task_id IS NOT NULL AND upload_task_id != '__uploading__';
```

## Зависимости

- `core.intern_utils`, `core.celery_task_status`
- `interviews.models` — Interview
- `interns.models` — Intern
- Celery, Redis, `boto3` (`core.s3_video_storage`); `yadisk` — только старые ссылки на видео

## Логирование

Логгер `interns_portal`, файл `logs/interns_portal.log` (RotatingFileHandler).

Загрузка видео помечается префиксом **`[PORTAL_UPLOAD]`** с полем `phase` (`request_start`, `tmp_saved`, `celery_dispatched`, `worker_start`, `worker_done`, `worker_failed_final` и др.). Email в логах не пишется.

**Пример фильтра в Loki/Grafana:**

```
{job="interview_management"} |= "[PORTAL_UPLOAD]" |= "interview_id=123"
```

**Операционно:** сброс зависших слотов в БД:

```sql
UPDATE interviews SET upload_task_id = '' WHERE upload_task_id = '__uploading__';
```

Проверка Celery/Redis после смены пароля: `CELERY_BROKER_URL` / `REDIS_URL` с паролем, если задан `REDIS_PASSWORD`.

## Тесты

- `tests/test_interns_portal/test_api.py` — REST API портала
- `tests/test_interns_portal/test_auth.py` — права `IsInternPortalStudent`
- `tests/test_interns_portal/test_tasks.py` — `upload_video_to_s3`
- `tests/test_core/test_s3_video_storage.py` — presign, parse URL
- `tests/test_interns_portal/test_video_upload_race.py` — гонки и сброс sentinel
- `tests/test_interns_portal/test_portal_upload_logging.py` — `[PORTAL_UPLOAD]`

Запуск: `pytest tests/test_interns_portal/ -v`
