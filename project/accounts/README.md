# accounts

Локальный вход демо-учётками. Остальной UI — React SPA.

## Назначение

- Выход и старый адрес `/accounts/login/` ведут на страницу портала `/login`.
- REST `POST /api/auth/login/` заполняет сессию.
- `KeycloakUser` собирается из групп в сессии.
- При входе менеджера создаётся или обновляется `managers.Manager`.

## Структура

```
accounts/
├── demo_users.py
├── views.py
├── api_views.py
├── authentication.py
├── permissions.py
└── sso_user.py
```

## URL

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/accounts/login/` | Редирект на `/login` |
| GET | `/accounts/logout/` | Выход |
| POST | `/accounts/logout-beacon/` | Выход без редиректа |
| POST | `/api/auth/login/` | Вход для SPA |

Демо: `admin` / `demo-admin`, `manager` / `demo-manager`, `student` / `demo-student`.

## Тесты

`pytest tests/test_accounts/ -v`
