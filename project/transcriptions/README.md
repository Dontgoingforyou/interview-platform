# transcriptions

Автоматическая транскрипция видеозаписей собеседований через Deepgram. Текст хранится в `InterviewTranscription`; семантический поиск — через `vector_search`. HTTP API — actions в `interviews.api.InterviewViewSet`, не отдельные Django-URL приложения.

## Назначение

- Транскрипция с Яндекс Диска (Deepgram Nova-2): диризация спикеров (`diarize`, `utterances`).
- Очередь без дублей: cooldown для `pending`, `select_for_update`, `transaction.on_commit`; stale `processing` — heartbeat и таймауты из `constants.py`.
- Две попытки при `408 SLOW_UPLOAD`: URL Deepgram, затем потоковая загрузка бинарных данных.
- Автозапуск по сигналу `post_save` на `Interview` при появлении `transcription_media_url`.
- Ручной запуск — `POST /api/interviews/{id}/transcribe/` (администратор или ментор). Статус и текст читают менеджер по своим записям, а также админ, HR и outstaff.
- Circuit breaker при нулевом балансе Deepgram (Redis).
- Пакетная обработка: `manage.py transcribe_interviews` (`--dry-run`, `--reset-balance-flag`).
- Баланс Deepgram: `GET /api/transcriptions/deepgram-balance/`.

## Структура

```
transcriptions/
├── apps.py
├── models.py                      # InterviewTranscription
├── constants.py                   # cooldown, stale, heartbeat
├── services.py                    # TranscriptionService
├── tasks.py                       # transcribe_interview (Celery)
├── interview_transcription_handlers.py  # очередь, статус, текст (для InterviewViewSet)
├── transcription_download_filename.py
├── signals.py                     # post_save Interview
└── management/commands/
    └── transcribe_interviews.py
```

## Модели

**InterviewTranscription** (OneToOne → Interview): `status` (`pending`, `processing`, `completed`, `failed`), `text`, `error_message`, `created_at`, `updated_at`. Таблица `interview_transcriptions`.

Источник медиа: свойство `Interview.transcription_media_url` — `video_link` или публичная ссылка на файл с Яндекс.Диска в `link` / `interview_link`.

## URL и представления

Эндпоинты в `interviews/api/` (префикс `/api/interviews/`):

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| POST | `/api/interviews/{id}/transcribe/` | Администратор или ментор | Запуск/перезапуск транскрипции |
| GET | `/api/interviews/{id}/transcription-status/` | Менеджер (свои) / админ, HR, outstaff | Статус (JSON) |
| GET | `/api/interviews/{id}/transcription-text/` | То же | Текст транскрипции |
| GET | `/api/transcriptions/deepgram-balance/` | Админ | Баланс Deepgram |

Логика ответов — `transcriptions.interview_transcription_handlers`.

## Доступ

- `transcribe` — `IsAdminOrMentorRole`.
- Статус и текст — менеджер видит только свои собеседования; админ, HR, outstaff — любые.
- Аутентификация: сессия локального входа (см. `accounts`).

## Зависимости

- `interviews` — модель Interview, ViewSet
- `vector_search` — эмбеддинг типа `interview_transcription`
- Deepgram API (`deepgram-sdk`), Яндекс Диск (`yadisk`), Celery, Redis

## Конфигурация

Переменные окружения: `DEEPGRAM_API_KEY`, `DEEPGRAM_PROJECT_ID`, `YA_TOKEN`. Имена — в `.env.example`.

## Работа в Docker

```bash
docker exec interview_management_web_local python manage.py transcribe_interviews --dry-run
docker exec interview_management_web_local python manage.py transcribe_interviews --limit=100
docker exec interview_management_web_local python manage.py transcribe_interviews --reset-balance-flag
```

## Логирование

Логгер `transcriptions`, файл `logs/transcriptions.log`.

## Тесты

- `tests/test_transcriptions/test_models.py` — InterviewTranscription
- `tests/test_transcriptions/test_services.py` — TranscriptionService, Deepgram
- `tests/test_transcriptions/test_tasks.py` — Celery, сигналы
- `tests/test_transcriptions/test_handlers.py` — handlers для InterviewViewSet
- `tests/test_transcriptions/test_ssrf.py` — проверка URL
- `tests/test_transcriptions/test_transcription_download_filename.py` — имена файлов

Запуск: `pytest tests/test_transcriptions/ -v`
