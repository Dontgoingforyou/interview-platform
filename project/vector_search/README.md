# vector_search

Семантический поиск по сущностям платформы (pgvector + OpenAI-эмбеддинги). Индексация через signals и Celery. UI — React; API под `/api/vector/` (вне catch-all SPA).

## Назначение

- Семантический поиск по естественному языку.
- Похожие сущности по `entity_type` + `entity_id`.
- Статистика векторизованных данных.
- Типы: interview, intern, offer, debt, sad_intern, manager, company, direction, intern_weekly_status, interview_transcription, kb_article. Один список `VECTOR_ENTITY_TYPES` в `utils.py` используют команды `vectorize_data`, `vectorize_async` и `check_vector_sync`.

## Структура

```
vector_search/
├── models.py              # VectorEmbedding, SearchLog
├── services.py
├── tasks.py
├── signals.py
├── serializers.py
├── utils.py
├── api/
│   ├── urls.py
│   └── views.py
├── api_urls.py
└── management/commands/
    ├── vectorize_data.py
    ├── vectorize_async.py
    └── check_vector_sync.py
```

`check_vector_sync` сравнивает строки в БД и эмбеддинги. `--fix` ставит переиндексацию пропущенных.

## Модели

**VectorEmbedding:** `entity_type`, `entity_id`, `text_content`, `embedding` (1536), `metadata`, timestamps. unique `(entity_type, entity_id)`.

**SearchLog:** запрос, фильтры, `results_count`, `search_time_ms`, обезличенный идентификатор пользователя, `created_at`.

## URL и представления

Только REST API (префикс `/api/vector/`, подключается до React catch-all).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| POST | `/api/vector/search/` | Менеджер/Админ | Семантический поиск |
| POST | `/api/vector/similar/` | То же | Похожие сущности |
| GET | `/api/vector/stats/` | То же | Статистика |

Приложение опционально (`DISABLE_VECTOR` убирает из `INSTALLED_APPS`).

## Доступ

- `IsManagerOrAdmin`, локальная сессия.

## Зависимости

- PostgreSQL + pgvector, OpenAI API, Celery, Redis
- Доменные модели всех перечисленных приложений

## Тесты

- `tests/test_vector_search/test_models.py` — VectorEmbedding
- `tests/test_vector_search/test_services.py` — поиск и эмбеддинги
- `tests/test_vector_search/test_tasks.py` — Celery
- `tests/test_vector_search/test_signals.py` — индексация
- `tests/test_vector_search/test_serializers.py` — сериализаторы
- `tests/test_vector_search/test_utils.py` — утилиты
- `tests/test_vector_search/test_api_views.py` — REST API
- `tests/test_vector_search/test_check_vector_sync_command.py` — `check_vector_sync`
- `tests/test_vector_search/test_vectorize_async_command.py` — `vectorize_async`

Запуск: `pytest tests/test_vector_search/ -v`
