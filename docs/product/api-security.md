# Безопасность API

Сессия появляется после локального входа. Демо-учётки задаются в `project/accounts/demo_users.py`.

## Роли

| Роль | Права |
|---|---|
| `role_admin` | Чтение, запись и удаление |
| `employment-managers`, `cv-managers`, `education` | Чтение своих данных |

Менеджер видит записи, где `manager_email` совпадает с почтой из сессии. Администратор видит все.

## Эндпоинты

| Метод | URL | Кто |
|---|---|---|
| GET | `/api/interviews/` | менеджер и администратор |
| POST, PATCH, DELETE | `/api/interviews/` | администратор |
| GET | `/api/interns/`, `/api/hr/` | менеджер и администратор |
| GET | `/api/managers/` | администратор |
| GET / POST | `/api/debts/`, `/api/employees/`, `/api/sad-interns/` | чтение — менеджер, запись — администратор |

Типы собеседований: `screening`, `tech`, `hr`, `final`, `mock`, `test`, `tech_questionnaire`, `cancelled`.

Документация `/api/docs/`, `/api/redoc/` и схема `/api/schema/` отдаются при `DEBUG=True` после входа менеджера или администратора. Студент портала получает 403.

Без сессии API отвечает 401. С сессией, но без нужной роли — 403. При превышении лимита — 429. Лимиты задаются в `settings.py`.
