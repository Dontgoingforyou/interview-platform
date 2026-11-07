# Безопасность API

## Обзор

API использует сессию локального входа.

Демо-учётки задаются в `project/accounts/demo_users.py`.

## Роли и доступ

| Роль | Права |
|---|---|
| `role_admin` | Полный доступ (чтение + запись + удаление) |
| `employment-managers` | Чтение своих данных |
| `cv-managers` | Чтение своих данных |
| `education` | Чтение своих данных |

Менеджеры видят **только своих** студентов (фильтрация по `manager_email` из сессии).
Администраторы видят **все** данные.

## Доступные API-эндпоинты

| Метод | URL | Права |
|---|---|---|
| GET | `/api/interviews/` | `IsManagerOrAdmin` |
| POST | `/api/interviews/` | `IsAdminRole` |
| GET | `/api/interviews/{id}/` | `IsManagerOrAdmin` |
| PATCH | `/api/interviews/{id}/` | `IsAdminRole` |
| DELETE | `/api/interviews/{id}/` | `IsAdminRole` |
| GET | `/api/hr/` | `IsManagerOrAdmin` |
| GET | `/api/hr/{id}/` | `IsManagerOrAdmin` |
| GET | `/api/interns/` | `IsManagerOrAdmin` |
| GET | `/api/managers/` | `IsAdminRole` |
| GET/POST | `/api/debts/` | `IsManagerOrAdmin` / `IsAdminRole` |
| GET/POST | `/api/employees/` | `IsManagerOrAdmin` / `IsAdminRole` |
| GET/POST | `/api/sad-interns/` | `IsManagerOrAdmin` / `IsAdminRole` |

Менеджер видит только **свои** записи (фильтрация по `manager_email` из сессии).

### Типы собеседований (interview_type)

| Значение | Название |
|---|---|
| `screening` | Скрининг |
| `tech` | Техническое собеседование |
| `hr` | HR собеседование |
| `final` | Финальное собеседование |
| `mock` | МОК собеседование |
| `test` | Тестовое задание |
| `tech_questionnaire` | Анкета с большим кол-вом технички |
| `cancelled` | НЕ СОСТОЯЛОСЬ |

## Примеры запросов

### curl

```bash
# Список студентов (сессия в куке)
curl -b "sessionid=<session>" http://localhost:82/api/interns/

# Список собеседований
curl -b "sessionid=<session>" http://localhost:82/api/interviews/

# Список собеседований с фильтрацией по типу
curl -b "sessionid=<session>" \
  "http://localhost:82/api/interviews/?interview_type=screening&date_from=2025-01-01"

# Список HR-специалистов
curl -b "sessionid=<session>" http://localhost:82/api/hr/
```

### Python (requests)

```python
import requests

session = requests.Session()
session.cookies.set("sessionid", "<session>")
BASE_URL = "http://localhost:82/api"

# Список студентов
response = session.get(f"{BASE_URL}/interns/")
print(response.json())

# Список собеседований с фильтрацией
response = session.get(
    f"{BASE_URL}/interviews/",
    params={"date_from": "2025-01-01", "date_to": "2025-12-31", "interview_type": "tech"}
)
print(response.json())

# Список HR-специалистов
response = requests.get(f"{BASE_URL}/hr/", headers=HEADERS)
print(response.json())
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:82/api';

const response = await fetch(`${BASE_URL}/interviews/`, {
    credentials: 'include',
});
const data = await response.json();
console.log(data);
```

## Swagger UI

`/api/docs/`, `/api/redoc/` и OpenAPI-схема `/api/schema/` отдаются **только при `DEBUG=True`** (локальная разработка). При `DEBUG=False` эти пути отвечают 404, в том числе менеджеру. На включённой документации доступ есть только у менеджеров и администраторов. Пользователи с ролью «студент» (портал interns_portal) получают 403 Forbidden.

1. Запустите приложение с `DEBUG=True` и откройте `http://localhost:82/api/docs/` (после входа демо-учёткой менеджера или админа)
2. Нажмите кнопку **Authorize** в правом верхнем углу
3. Войдите демо-учёткой: сессия уходит кукой `sessionid`.
4. Нажмите **Authorize**

Токен не нужен: после входа через `/login` запросы идут с кукой сессии.

## Rate Limiting

| Тип пользователя | Поведение |
|---|---|
| Без сессии (анонимный) | `401 Unauthorized` — доступ запрещён |
| С сессией | Стандартный DRF throttling (настраивается в `settings.py`) |

## CORS

Настроен в `settings.py`. Для production указать конкретные домены вместо `CORS_ALLOW_ALL_ORIGINS`.

## Production-чеклист

- `DEBUG=False` в `.env`
- `SECRET_KEY` — случайная строка (не дефолтная)
- HTTPS обязателен
- `CORS_ALLOW_ALL_ORIGINS=False`, перечислить конкретные домены
- Сессия входа хранится в httpOnly-куке

## Коды ответов

| Код | Причина |
|---|---|
| `401 Unauthorized` | Сессия отсутствует или недействительна |
| `403 Forbidden` | Сессия есть, но недостаточно прав (не та роль) |
| `429 Too Many Requests` | Превышен rate limit |
