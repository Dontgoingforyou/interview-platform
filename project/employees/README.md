# employees

Раздел «Сотрудники»: список менеджеров, доска менеджера со студентами и недельной статистикой собеседований, админ-отчёты KPI и разработчиков. UI — React SPA; все эндпоинты под `/api/employees/...` (включая legacy JSON, ранее `/employees/api/`).

## Назначение

- Список активных менеджеров и поиск студента по имени.
- Доска менеджера: студенты, 6 недель собеседований, коэффициент активности, архив по месяцам, статусы отсутствия.
- CRUD `InternWeeklyStatus` (ручная корректировка собесов — админ).
- Админ: KPI за период, отчёт по разработчикам у менеджеров, скрытие/восстановление менеджера.
- Обновление `manual_status` студента — также через `PATCH /api/interns/{id}/manual-status/` (приложение `interns`).

## Структура

```
employees/
├── models.py              # InternWeeklyStatus
├── api_views.py           # SearchIntern, UpdateStatus, недели, set-manager-active
├── serializers.py
├── services.py            # ManagerDetailService
├── board_serialization.py
├── api/
│   ├── urls.py
│   ├── weekly_status_api.py
│   ├── admin_api_views.py
│   └── board_api_views.py
└── api_urls.py
```

## Модели

**InternWeeklyStatus:** `intern` (FK), `week_start` (понедельник), `manual_interview_count`, `absence_status`, `absence_notes`. unique_together `(intern, week_start)`.

## URL и представления

Только REST API (префикс `/api/`).

| Метод | URL | Доступ | Описание |
|-------|-----|--------|----------|
| GET | `/api/employees/managers/` | Менеджер/Админ | Список менеджеров (карточки) |
| GET | `/api/employees/managers/<email>/board/` | Менеджер/Админ | Доска менеджера |
| GET | `/api/employees/search-intern/` | Менеджер/Админ | Поиск студента по имени |
| POST | `/api/employees/update-status/` | Менеджер/Админ | Обновление статуса студента (legacy) |
| POST | `/api/employees/update-week-interviews/` | Админ | Корректировка собесов за неделю |
| POST | `/api/employees/update-week-absence/` | Менеджер/Админ | Статус отсутствия за неделю |
| POST | `/api/employees/set-manager-active/` | Админ | Скрыть/восстановить менеджера |
| GET/POST/PATCH/DELETE | `/api/employees/weekly-statuses/` | Менеджер/Админ | CRUD недельных статусов |
| GET | `/api/employees/admin/kpi/` | Админ | KPI (`date_from`, `date_to`, `min_kpi`) |
| GET | `/api/employees/admin/developers/` | Админ | Разработчики по менеджерам |

## Доступ

- DRF: `IsManagerOrAdmin`; админ-only — KPI, developers, update-week-interviews, set-manager-active.
- Менеджер работает только со своими студентами (`manager_email`).

## Зависимости

- `core.mixins`, `interns`, `interviews`, `managers`, `directions`

## Тесты

- `tests/test_employees/test_api_views.py` — legacy JSON и weekly-statuses
- `tests/test_employees/test_admin_api_views.py` — KPI, developers
- `tests/test_employees/test_board_api_views.py` — managers, board
- `tests/test_employees/test_intern_status_logic.py` — логика статусов студентов

Запуск: `pytest tests/test_employees/ -v`
