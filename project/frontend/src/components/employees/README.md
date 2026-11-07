# Раздел «Сотрудники» (React) — архитектура

Цель: **тонкие страницы** (`pages/employees/*`) только склеивают данные и секции; вся разметка и локальная логика UI — в `components/employees/*`.

## Слои и зависимости (строго сверху вниз)

1. **`pages/employees/`** — маршрут, хуки данных (`useEmployeesManagers`, `useManagerBoard`, TanStack Query на странице), проверка роли admin, модалки уровня страницы. **Не** содержит разметку таблиц отчётов, доски менеджера, панели поиска.
2. **`components/employees/`** — презентация по зонам:
   - `list/` — индекс менеджеров: поиск студента, таблица менеджеров
   - `board/` — доска менеджера: таблицы по неделям/месяцам, ячейки недели, селект статуса, модалка отсутствия
   - `admin/` — админ-отчёты (KPI по периоду, количество разработчиков у менеджеров)
3. **`hooks/employees/`** — переиспользуемые запросы к API доски и списка менеджеров. **Не** импортируют компоненты из `components/employees`.
4. **`api/employeesApi.ts`**, **`api/managersApi.ts`**, **`api/internsApi.ts`**, **`types/employee.ts`** — контракт с бэкендом.
5. **`utils/employees/`** — чистые функции для сотрудников (напр. **`employeeBoard.ts`** для доски). См. **`.cursor/rules/react-frontend.mdc`** → «Утилиты».

**Запрещено:** компоненты из `components/employees` импортируют файлы из `pages/`.

## Утилиты именно этой фичи

Хелперы сотрудников в **`src/utils/employees/`**.

## Текущая структура папок компонентов

```
components/employees/
  README.md
  admin/
    AdminDevelopersInternList.tsx
    AdminDevelopersReport.tsx
    AdminKpiDetailsTable.tsx
    AdminKpiFiltersForm.tsx
    AdminKpiResultsSection.tsx
  board/
    EmployeeAbsenceModal.tsx
    EmployeeInternTable.tsx
    EmployeeMonthTables.tsx
    EmployeeStatusSelect.tsx
    EmployeeWeekCell.tsx
  list/
    EmployeeInternSearchPanel.tsx
    EmployeeManagersIndexTable.tsx
```

Общие UI-атомы (`Pagination`, `TableScroll`, `CollapsibleSection`, `PageIntroCard`) — в `components/ui/`.
