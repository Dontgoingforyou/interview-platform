# Менеджеры (React)

Фича дашборда `/managers`: KPI, графики Recharts, таблица, текстовые наблюдения.

**Бэкенд:** эндпоинты DRF, сервис таблицы и legacy-шаблоны — в [корневом `managers/README.md`](../../../../managers/README.md).

## Слои

| Папка | Назначение |
|-------|------------|
| `analytics/` | Сетка метрик (`ManagersMetricsMainGrid`), общие компоненты из `interviews/` |
| `charts/` | Recharts: топ по интервью, сводка активности команды |
| `list/` | Таблица (desktop) и карточки (mobile) |
| `observations/` | Блок наблюдений (данные + `utils/managers/managersObservationsText`) |

## Данные

- API: `api/managersApi.ts` — `getManagersAnalytics`, `getManagersObservations`, `getManagersDashboardTable`
- Хук: `hooks/managers/useManagersDashboard.ts`
- Типы: `types/managerDashboard.ts`
- Конфиг метрик: `constants/managerMetrics.ts`
- Стили страницы: `styles/managers.css`

Страница: `pages/managers/ManagersListPage.tsx` (подключается через `React.lazy` в `appRoutes.tsx`).
