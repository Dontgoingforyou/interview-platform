# Компоненты раздела «Долги»

Структура по аналогии с `components/interviews/` и `components/interns/`.

## Подпапки

- **`analytics/`** — сетка метрик (`DebtMetricsMainGrid`), данные из `GET /api/analytics/debts/`.
- **`filters/`** — `DebtFilters` (список), `DebtByMonthFiltersForm` (отчёт по месяцам).
- **`list/`** — таблица/карточки/скелетон списка и таблица «по месяцам».

## Импорты

- Доменные утилиты — **`src/utils/debts/`** (`debtListParams`, `debtTableDisplay`, …).
- Страницы (`pages/debts/`) импортируют компоненты и хуки; **не наоборот**.
- Общие виджеты метрик — `components/ui/` (`MetricCard`, `MetricAnimatedStrong`, `MetricInfoIcon`).
