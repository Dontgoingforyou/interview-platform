# <имя_приложения>

Краткое описание в 1–3 предложениях: что делает приложение и для кого.

## Назначение

- Основная возможность 1
- Основная возможность 2
- Основная возможность 3

## Структура

```
<app>/
├── models.py          # Описание
├── views.py           # Описание
├── urls.py
├── forms.py           # при необходимости
├── services.py        # при необходимости
├── api_views.py       # при наличии REST API
├── api_urls.py
├── serializers.py
├── migrations/
└── templates/<app>/
    ├── list.html
    └── form.html
```

## Модели

Таблица полей или краткое описание. Без полного кода и choices.

| Поле | Тип | Описание |
|------|-----|----------|
| … | … | … |

## URL и представления

| URL | View | Описание |
|-----|------|----------|
| `/<app>/` | …ListView | Список |
| `/<app>/new/` | …CreateView | Создание |
| `/<app>/<pk>/edit/` | …UpdateView | Редактирование |
| `/<app>/<pk>/delete/` | …DeleteView | Удаление |

### REST API (если есть)

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/<app>/` | … | Список |

## Доступ

- Миксин: `…RequiredMixin` (из `core.mixins` или `accounts`).
- Кто имеет доступ: одна строка.

## Зависимости

- `core` — миксины, базовые вьюхи
- `<другое_приложение>` — модель X
- Celery / Redis — при необходимости

## Тесты

- `tests/test_<app>/test_views.py` — представления, доступ
- `tests/test_<app>/test_models.py` — модели
- `tests/test_<app>/test_api_views.py` — REST API

Запуск: `pytest tests/test_<app>/ -v`
