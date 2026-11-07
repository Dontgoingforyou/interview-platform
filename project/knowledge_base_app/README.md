# knowledge_base_app

База знаний на Markdown: разделы и статьи в БД (`KBSection`, `KBArticle`). Просмотр — менеджеры; создание и редактирование разделов и статей — админ. UI — React SPA; бэкенд — только `/api/knowledge-base/...`.

## Назначение

- CRUD разделов и статей через REST API.
- Поиск по заголовкам и содержимому.
- `KnowledgeBaseManager` — ORM, Markdown → HTML, санитизация (XSS).

## Структура

```
knowledge_base_app/
├── models.py          # KBSection, KBArticle
├── managers.py        # KnowledgeBaseManager
├── api/
│   ├── urls.py
│   └── views.py
├── api_urls.py
├── serializers.py
├── decorators.py      # @admin_required_api
├── utils.py
├── constants.py
└── apps.py
```

## Модели

- **KBSection** — `section_id`, `title`, `description`, `icon`, `order`, `visible`, timestamps. Таблица `knowledge_base_sections`.
- **KBArticle** — FK на раздел, `filename`, `title`, `content` (Markdown), timestamps. Уникальность `(section, filename)`. Таблица `knowledge_base_articles`.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/knowledge-base/search/` | Менеджер | Поиск |
| GET/POST | `/api/knowledge-base/sections/` | GET — менеджер; POST — админ | Список / создание раздела |
| GET/PUT/PATCH/DELETE | `/api/knowledge-base/sections/<section_id>/` | GET — менеджер; запись — админ | Раздел |
| GET/POST | `/api/knowledge-base/sections/<section_id>/articles/` | GET — менеджер; POST — админ | Список / создание статьи |
| GET/PUT/PATCH/DELETE | `/api/knowledge-base/sections/<section_id>/articles/<filename>/` | GET — менеджер; запись — админ | Статья |

## Доступ

- Просмотр и поиск: `IsManagerOrAdmin`.
- Создание/изменение/удаление разделов и статей: `IsAdminRole` (декораторы `@admin_required_api` в API-вьюхах).

## Зависимости

- `accounts.permissions`
- `markdown`, `bleach` — рендер и санитизация

## Тесты

- `tests/test_knowledge_base_app/test_managers.py` — менеджер: разделы, статьи, поиск, санитизация
- `tests/test_knowledge_base_app/test_api_views.py` — REST API

Запуск: `pytest tests/test_knowledge_base_app/ -v`
